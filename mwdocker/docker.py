'''
Created on 2021-08-06

@author: wf
'''
from python_on_whales import docker
import os
import datetime
import time
import secrets
import socket
import re
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound
import mysql.connector
from mysql.connector import Error
from pathlib import Path
from wikibot.wikiuser import WikiUser
    
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

    def __init__(self,user:str,password:str,name="mediawiki",version="1.35.2",extensionMap:dict={},wikiId:str=None,mariaDBVersion="10.5",smwVersion=None,port=9080,sqlPort=9306,mySQLRootPassword=None,debug=False,verbose=True):
        '''
        Constructor
        
        Args:
            user(str): the initial sysop user to create
            password(str): the initial sysop password to user
            version(str): the  MediaWiki version to create docker applications for
            extensionMap(dict): a map of extensions to be installed
            wikiId(str): the wikiId to create a py-3rdparty-mediawiki user for (if any)
            sqlPort(int): the base port to be used for  publishing the SQL port (3306) for the docker applications
            port(int): the port to be used for publishing the HTML port (80) for the docker applications
            networkName(str): the name to use for the docker network to be shared by the cluster participants
            mariaDBVersion(str): the Maria DB version to install as the SQL database provider for the docker applications
            smwVersion(str): Semantic MediaWiki Version to be used (if any)
            mySQLRootPassword(str): the mySQL root password to use for the database containers - if None a random password is generated
            debug(bool): if True debugging is enabled
            verbose(bool): if True output is verbose
        '''
        # identifications
        self.name=name
        self.user=user
        self.password=password
        self.wikiId=wikiId
        # extensions
        self.extensionMap=extensionMap
        # Versions
        self.version=version
        self.fullVersion=f"MediaWiki {self.version}"
        self.smwVersion=smwVersion
        self.underscoreVersion=version.replace(".","_")
        self.shortVersion=self.getShortVersion()
        self.mariaDBVersion=mariaDBVersion
        # hostname and ports
        self.hostname=socket.getfqdn()
        self.port=port
        self.url=f"http://{self.hostname}:{self.port}"
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
        self.dbUser="wikiuser"
        self.wikiUser=None
       
    @staticmethod 
    def check()->str:
        errMsg=None
        if not docker.compose.is_installed():
            errMsg="""docker composer up needs to be working
            you might want to install https://github.com/docker/compose-cli
            Compose v2 can be installed manually as a CLI plugin, 
            by downloading latest v2.x release from https://github.com/docker/compose-cli/releases for your architecture and move into ~/.docker/cli-plugins/docker-compose
"""
        return errMsg
        
            
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
        scriptdir=os.path.dirname(os.path.realpath(__file__))
        resourcePath=os.path.realpath(f"{scriptdir}/resources")
        template_dir = os.path.realpath(f'{resourcePath}/templates')
        #print(f"jinja template directory is {template_dir}")
        home = str(Path.home())
        self.dockerPath=f'{home}/.pymediawikidocker/mw{self.underscoreVersion}' 
        os.makedirs(self.dockerPath,exist_ok=True)
        env = Environment(loader=FileSystemLoader(template_dir))
        return env
    
    def initDB(self):
        '''
        initialize my SQL database
        '''
        # restore the mySQL dump data
        self.execute("/tmp/initdb.sh")
        # update the database e.g. to initialize Semantic MediaWiki tables
        self.execute("/tmp/update.sh")
        # add an initial sysop user as specified
        self.execute("/tmp/addSysopUser.sh")
        # if wikiId is specified create a wikiuser
        if self.wikiId is not None:
            self.wikiUser=self.createWikiUser(store=True)
            
    def installExtensions(self):
        '''
        install all extensions
        '''
        self.execute("/tmp/installExtensions.sh")
            
            
    def createWikiUser(self,store:bool=False):
        '''
        create my wikiUser and optionally save it
        
        Args:
           store(bool): if True save my user data to the relevant ini File
        '''
        if self.wikiId is None:
            raise("createWikiUser needs wikiId to be set but it is None")
        userDict={
            "wikiId":f"{self.wikiId}",
            "url": f"{self.url}",
            "scriptPath": "",
            "user": f"{self.user}",
            "email":"noreply@nouser.com",
            "version": f"{self.fullVersion}",
            "password": f"{self.password}"
        }
        wikiUser=WikiUser.ofDict(userDict,encrypted=False)
        if store:
            wikiUser.save()
        return wikiUser
    
    def execute(self,command):
        '''
        execute the given command
        '''
        if self.mwContainer:
            docker.execute(container=self.mwContainer,command=command)
        else:
            raise Exception(f"no mediawiki Container for {self.name}")
    
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
                print (f"Connection to {self.database} on {self.host} with user {self.dbUser} not established" )
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
        
        Args:
            timeout(int): number of seconds for timeout
        '''
        if self.dbConn is None:
            try:
                self.dbConn = mysql.connector.connect(host=self.host,
                                 database=self.database,
                                 user=self.dbUser,
                                 port=self.sqlPort,
                                 password=self.mySQLPassword,
                                 connection_timeout=timeout)
        
            except Error as e :
                print (f"Connection to {self.database} on {self.host} with user {self.dbUser} failed error: {str(e)}" )
        return self.dbConn
    
    def doCheckDBConnection(self,timeout:int=10)->bool:
        '''
        check the database connection of this application
        '''       
        ok=False
        self.dbConnect(timeout=timeout)
        if self.dbConn and self.dbConn.is_connected():
            rows=self.sqlQuery("select database();")
            ok=True
            if self.verbose:
                print (f"Connection to {self.database} on {self.host} with user {self.dbUser} established database returns: {rows[0]}")
        return ok
    
    def checkDBConnection(self,timeout:float=10,initialSleep:float=2.5,maxTries:int=6)->bool:
        '''
        check database connection with retries
        
        Args:
            timeout(float): number of seconds for timeout
            initialSleep(float): number of seconds to initially wait/sleep
            maxTries(int): maximum number of retries before giving up between each try a sleep is done that starts
            with 0.5 secs and doubles on every retry
            
        Returns:
            bool: if connection was successful
        '''
        if self.debug:
            print (f"Trying DB-Connection to {self.database} on {self.host} port {self.sqlPort} with user {self.dbUser} with max {maxTries} tries and {timeout}s timeout per try - initial sleep {initialSleep}s")
        time.sleep(initialSleep)
        sleep=0.5
        tries=1
        ok=False
        while not ok and tries<=maxTries:
            ok=self.doCheckDBConnection(timeout=timeout)
            if not ok:
                if self.verbose:
                    print(f"Connection attempt #{tries} failed will retry in {sleep} secs" )
                tries+=1    
                # wait before trying
                time.sleep(sleep)
                sleep=sleep*2
        return ok
    
    def generate(self,templateName:str,targetPath:str,**kwArgs):
        '''
        generate file at targetPath using the given templateName
        
        Args:
            templateName(str): the Jinja2 template to use
            targetPath(str): the path to the target file
            kwArgs(): generic keyword arguments to pass on to template rendering
        
        '''
        try:
            template = self.env.get_template(templateName)
            timestamp=datetime.datetime.now().isoformat()
            content=template.render(mwVersion=self.version,mariaDBVersion=self.mariaDBVersion,port=self.port,sqlPort=self.sqlPort,smwVersion=self.smwVersion,timestamp=timestamp,**kwArgs)
            with open(targetPath, "w") as targetFile:
                targetFile.write(content)
        except TemplateNotFound:
            print(f"no template {templateName} for {self.name} {self.version}")     
        
    def getShortVersion(self):
        '''
        get my short version e.g. convert 1.27.7 to 127
        
        Returns:
            str: the short version string
        '''
        versionMatch=re.match("(?P<major>[0-9]+)\.(?P<minor>[0-9]+)",self.version)
        shortVersion=f"{versionMatch.group('major')}{versionMatch.group('minor')}"
        return shortVersion
             
    def generateAll(self):
        '''
        generate all files needed for the docker handling
        '''
        self.generate("mwDockerfile",f"{self.dockerPath}/Dockerfile")
        self.generate("mwCompose.yml",f"{self.dockerPath}/docker-compose.yml",mySQLRootPassword=self.mySQLRootPassword,mySQLPassword=self.mySQLPassword)
        self.generate(f"mwLocalSettings{self.shortVersion}.php",f"{self.dockerPath}/LocalSettings.php",mySQLPassword=self.mySQLPassword,hostname=self.hostname,extensions=self.extensionMap.values())
        self.generate(f"mwWiki{self.shortVersion}.sql",f"{self.dockerPath}/wiki.sql")
        self.generate(f"addSysopUser.sh",f"{self.dockerPath}/addSysopUser.sh",user=self.user,password=self.password)
        self.generate(f"installExtensions.sh",f"{self.dockerPath}/installExtensions.sh",extensions=self.extensionMap.values())
        for fileName in ["initdb.sh","update.sh","phpinfo.php","composer.local.json"]:
            self.generate(f"{fileName}",f"{self.dockerPath}/{fileName}")
        
        
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
            
