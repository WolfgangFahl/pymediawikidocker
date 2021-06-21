'''
Created on 2021-08-06

@author: wf
'''
from python_on_whales import docker
import os
import datetime
import secrets
import socket
import re
from jinja2 import Environment, FileSystemLoader
import mysql.connector
from mysql.connector import Error
    
class DockerMap():
    '''
    helper class to convert lists of docker elements to maps for improved
    lookup functionality
    '''
    @staticmethod
    def getContainerMap():
        '''
        get a map/dict of containers by container name
        '''
        containerMap={}
        for container in docker.container.list():
            containerMap[container.name]=container
            pass
        return containerMap
    
class DockerApplication(object):
    '''
    MediaWiki Docker image
    '''

    def __init__(self,name="mediawiki",version="1.35.2",mariaDBVersion="10.5",port=9080,sqlPort=9306,mySQLRootPassword=None,debug=False,verbose=True):
        '''
        Constructor
        '''
        self.name=name
        # Versions
        self.version=version
        self.underscoreVersion=version.replace(".","_")
        self.shortVersion=self.getShortVersion()
        self.mariaDBVersion=mariaDBVersion
        # ports
        self.port=port
        self.sqlPort=sqlPort
        # debug and verbosity
        self.debug=debug
        self.verbose=verbose
        # passwords
        password_length = 13
        if mySQLRootPassword is None:
            self.mySQLRootPassword=secrets.token_urlsafe(password_length)
        else:
            self.mySQLRootPassword=mySQLRootPassword
        self.mySQLPassword=secrets.token_urlsafe(password_length)
        # jinja and docker prerequisites
        self.env=self.getJinjaEnv()
        self.getContainers()
        self.dbConn=None
        self.database="wiki"
        self.host="localhost"
        self.user="wikiuser"
            
    def defaultContainerName(self):
        '''
        return the default container name which consists of the 
        my name with the version appended
        
        Returns
            str: the default container name
        '''
        return f"{self.name}_{self.version}"
    
    def getContainers(self):
        '''
        get my containers
        '''
        self.dbContainer=None
        self.mwContainer=None
        containerMap=DockerMap.getContainerMap()
        dbContainerName=f"mw{self.underscoreVersion}_db_1"
        mwContainerName=f"mw{self.underscoreVersion}_mw_1"
        if dbContainerName in containerMap:
            self.dbContainer=containerMap[dbContainerName]
        if mwContainerName in containerMap:
            self.mwContainer=containerMap[mwContainerName]
        
            
    def getJinjaEnv(self):
        '''
        get a Jinja2 environment
        '''
        scriptpath=os.path.realpath(__file__)
        resourcePath=os.path.realpath(f"{scriptpath}/../../resources")
        template_dir = os.path.realpath(f'{resourcePath}/templates')
        #print(f"jinja template directory is {template_dir}")
        self.dockerPath=f'{resourcePath}/mw{self.underscoreVersion}' 
        os.makedirs(self.dockerPath,exist_ok=True)
        env = Environment(loader=FileSystemLoader(template_dir))
        return env
    
    def close(self):
        self.dbClose()
    
    def sqlQuery(self,query):
        '''
        run the given SQL query
        '''
        if self.dbConn and self.dbConn.is_connected():
            cursor = self.dbConn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            return rows
        else:
            if self.verbose:
                print (f"Connection to {self.database} on {self.host} with user {self.user} not established" )
            return None
        
    def dbClose(self):
        '''
        close the database connection
        '''
        if self.dbConn and self.dbConn.is_connected():
            self.dbConn.close()
        
    def dbConnect(self,timeout:int=10):
        '''
        connect to the database and return the connection
        '''
        if self.dbConn is None:
            try:
                self.dbConn = mysql.connector.connect(host=self.host,
                                 database=self.database,
                                 user=self.user,
                                 port=self.sqlPort,
                                 password=self.mySQLPassword,
                                 connection_timeout=timeout)
        
            except Error as e :
                print (f"Connection to {self.database} on {self.host} with user {self.user} failed error: {str(e)}" )
        return self.dbConn
    
    def checkDBConnection(self,timeout:int=10)->bool:
        '''
        check the database connection of this application
        '''       
        ok=False
        self.dbConnect(timeout=timeout)
        if self.dbConn and self.dbConn.is_connected():
            rows=self.sqlQuery("select database();")
            ok=True
            if self.verbose:
                print ("You're connected to - ", rows[0])
        return ok
    
    def generate(self,templateName:str,targetPath:str,**kwArgs):
        '''
        generate file at targetPath using the given templateName
        
        Args:
            templateName(str): the Jinja2 template to use
            targetPath(str): the path to the target file
            kwArgs(): generic keyword arguments to pass on to template rendering
        
        '''
        template = self.env.get_template(templateName)
        timestamp=datetime.datetime.now().isoformat()
        content=template.render(mwVersion=self.version,mariaDBVersion=self.mariaDBVersion,port=self.port,sqlPort=self.sqlPort,timestamp=timestamp,**kwArgs)
        with open(targetPath, "w") as targetFile:
            targetFile.write(content)
      
    def genComposerFile(self,**kwArgs):  
        '''
        generate the composer file for 
        '''
        self.generate("mwCompose.yml",f"{self.dockerPath}/docker-compose.yml",mySQLRootPassword=self.mySQLRootPassword,mySQLPassword=self.mySQLPassword,**kwArgs)       
        
    def getShortVersion(self):
        '''
        get my short version e.g. convert 1.27.7 to 127
        
        Returns:
            str: the short version string
        '''
        versionMatch=re.match("(?P<major>[0-9]+)\.(?P<minor>[0-9]+)",self.version)
        shortVersion=f"{versionMatch.group('major')}{versionMatch.group('minor')}"
        return shortVersion
        
    def genDockerFile(self,**kwArgs):
        '''
        generate the docker files for this cluster
        '''
        self.generate("mwDockerfile",f"{self.dockerPath}/Dockerfile",**kwArgs)
        
    def genLocalSettings(self,**kwArgs):
        '''
        generate the local settings file
        '''
        hostname=socket.getfqdn()
        self.generate(f"mwLocalSettings{self.shortVersion}.php",f"{self.dockerPath}/LocalSettings.php",mySQLPassword=self.mySQLPassword,hostname=hostname,**kwArgs)
    
    def genWikiSQLDump(self,**kwArgs):
        '''
        generate the wiki SQL Dump
        '''
        self.generate(f"mwWiki{self.shortVersion}.sql",f"{self.dockerPath}/wiki.sql",**kwArgs)
        
    def genOther(self,**kwArgs):
        '''
        generate other files (mostly just copying)
        '''
        for fileName in ["initdb.sh","phpinfo.php"]:
            self.generate(f"{fileName}",f"{self.dockerPath}/{fileName}",**kwArgs)
        
    def generateAll(self):
        '''
        generate all files needed for the docker handling
        '''
        self.genDockerFile()
        self.genComposerFile()
        self.genLocalSettings()
        self.genWikiSQLDump()
        self.genOther()
        
    def up(self,forceRebuild:bool=False):
        '''
        start this docker application
        
        Args: 
            forceRebuild(bool): if true stop and remove the existing containers
        '''            
        if self.verbose:
            print(f"starting {self.name} {self.version} docker application ...")
        if forceRebuild:
            for container in [self.dbContainer,self.mwContainer]:
                if container is not None:
                    if self.verbose:
                        print(f"stopping and removing container {container.name}")
                    container.stop()
                    container.remove()

        # change directory so that docker CLI will find the relevant dockerfile and docker-compose.yml
        os.chdir(self.dockerPath)
        #project_config = docker.compose.config()
        if forceRebuild:
            docker.compose.build()
        # run docker compose up
        docker.compose.up(detach=True)    
        self.getContainers()
            
