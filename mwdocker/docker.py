'''
Created on 2021-08-06

@author: wf
'''
from python_on_whales import docker
import os
import platform
import datetime
import pprint
import time
import traceback
import typing
from jinja2 import Environment, FileSystemLoader
from jinja2.exceptions import TemplateNotFound
import mysql.connector
from mysql.connector import Error
from pathlib import Path
from wikibot3rd.wikiuser import WikiUser
from mwdocker.logger import Logger
from mwdocker.config import MwClusterConfig
from mwdocker.html_table import HtmlTables
from mwdocker.mariadb import MariaDB
from lodstorage.lod import LOD
from dataclasses import dataclass

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
    
class DockerContainer():
    """
    helper class for docker container info
    """
    
    def __init__(self,name,kind,container):
        """
        constructor
        """
        self.name=name
        self.kind=kind
        self.container=container
       
    def check(self):
        """
        check the given docker container
        
        print check message and Return if container is running
        
        Args:
            dc: the docker container
        
        Returns:
            bool: True if the container is not None
        """
        ok=self.container.state.running
        msg=f"mediawiki {self.kind} container {self.name}"
        return Logger.check_and_log(msg, ok) 
    
    def getHostPort(self,local_port:int=80)->int:
        """
        get the host port for the given local port
        
        Args:
            local_port(int): the local port to get the mapping for
            
        Returns:
            int: the  host port or None
        """
        host_port=None
        pb_dict=self.container.host_config.port_bindings
        p_local=f"{local_port}/tcp"
        if p_local in pb_dict:
            pb=pb_dict[p_local][0]
            host_port=pb.host_port
        return host_port
    
@dataclass
class DBStatus():
    """
    the Database Status
    """
    attempts: int
    max_tries: int
    ok: bool
    msg:str
    ex:typing.Optional[Exception]=None
        
class DockerApplication(object):
    '''
    MediaWiki Docker image
    '''

    def __init__(self,
                 config:MwClusterConfig):
        '''
        Constructor
        
        Args:
            config: MwClusterConfig,
            home: the home directory to use
        '''
        self.config=config
        # branch as need for git clone e.g. https://gerrit.wikimedia.org/g/mediawiki/extensions/MagicNoCache
        self.branch=f"REL{self.config.getShortVersion('_')}"
        self.composerVersion=1
        if self.config.shortVersion>="139":
            self.composerVersion=2
        # jinja and docker prerequisites
        self.env=self.getJinjaEnv()
        # docker file location
        self.dockerPath=f'{self.config.dockerPath}/{self.config.container_base_name}' 
        os.makedirs(self.dockerPath,exist_ok=True)
        
        self.getContainers()
        self.dbConn=None
        self.database="wiki"
        self.dbUser="wikiuser"
        self.wikiUser=None
       
    @staticmethod 
    def checkDockerEnvironment(debug:bool=False)->str:
        """
        check the docker environment
        
        Args:
            debug(bool): if True show debug information
            
        Returns:
            str: an error message or None
        """
        errMsg=None
        if not docker.compose.is_installed():
            errMsg="""docker composer up needs to be working"""
        os_path=os.environ["PATH"]
        paths=["/usr/local/bin"]
        for path in paths:
            if os.path.islink(f"{path}/docker"):
                if not path in os_path:
                    os.environ["PATH"]=f"{os_path}{os.pathsep}{path}"
                    if debug:
                        print(f"""modified PATH from {os_path} to \n{os.environ["PATH"]}""")
        return errMsg
    
    def check(self)->int:
        """
        check me
        
        Returns:
            int: exitCode: 0 if ok, 1 if not ok
        """
        DockerApplication.checkDockerEnvironment(self.config.debug) 
        exitCode=0
        mw,db=self.getContainers()
        if not mw:
            print("mediawiki container missing")
            exitCode=1
        if  not db:
            print("database container missing")
            exitCode=1
        if mw and db and mw.check() and db.check():
            host_port=mw.getHostPort(80)
            if host_port:
                Logger.check_and_log_equal(f"port binding",host_port,"expected  port",str(self.config.port))
                url=self.config.url
                # fix url to local port
                # @TODO isn't this superfluous / has no effect ...?
                url=url.replace(str(self.config.port),host_port)
                version_url=f"{url}/index.php/Special:Version"
                
                ok=self.checkWiki(version_url)
                if not ok:
                    exitCode=1
            else:
                self.log(f"port binding for port 80 missing",False)
                exitCode=1
            pass
        return exitCode
    
    def checkWiki(self,version_url:str)->bool:
        """
        check this wiki against the content of the given version_url
        """
        print(f"Checking {version_url} ...")
        ok=True
        try:
            html_tables=HtmlTables(version_url)
            tables=html_tables.get_tables("h2")
            if self.config.debug:
                p = pprint.PrettyPrinter(indent=2)
                p.pprint(tables)
            ok=ok and Logger.check_and_log("Special Version accessible ...", "Installed software" in tables)
            if ok:
                software=tables["Installed software"]
                software_map,_dup=LOD.getLookup(software, "Product", withDuplicates=False)
                mw_version=software_map["MediaWiki"]["Version"]
                ok=ok and Logger.check_and_log_equal("Mediawiki Version",mw_version,"expected ",self.config.version)
                db_version_str=software_map["MariaDB"]["Version"]
                db_version=MariaDB.getVersion(db_version_str)
                ok=ok and Logger.check_and_log(f"Maria DB Version {db_version} fitting expected {self.config.mariaDBVersion}?",self.config.mariaDBVersion.startswith(db_version))
                pass
        except Exception as ex:
            ok=Logger.check_and_log(str(ex), False)
        return ok
    
    def getContainerName(self,kind:str,separator:str):
        """
        get my container Name
        """
        containerName=f"{self.config.container_base_name}{separator}{kind}"
        return containerName
    
    def getContainers(self):
        """
        get my containers
        
        Returns:
            Tuple(
        """
        self.dbContainer=None
        self.mwContainer=None
        containerMap=DockerMap.getContainerMap()
        for separator in ["-","_"]:
            dbContainerName=self.getContainerName("db", separator)
            mwContainerName=self.getContainerName("mw", separator)
            if dbContainerName in containerMap:
                self.dbContainer=DockerContainer(dbContainerName,"database",containerMap[dbContainerName])
            if mwContainerName in containerMap:               
                self.mwContainer=DockerContainer(mwContainerName,"webserver",containerMap[mwContainerName])   
        return self.mwContainer,self.dbContainer   
            
    def getJinjaEnv(self):
        '''
        get a Jinja2 environment
        '''
        scriptdir=os.path.dirname(os.path.realpath(__file__))
        resourcePath=os.path.realpath(f"{scriptdir}/resources")
        template_dir = os.path.realpath(f'{resourcePath}/templates')
        #print(f"jinja template directory is {template_dir}")
        env = Environment(loader=FileSystemLoader(template_dir))
        return env
    
    def initDB(self):
        '''
        initialize my SQL database
        '''
        # restore the mySQL dump data
        self.execute("/root/initdb.sh")
        # update the database e.g. to initialize Semantic MediaWiki tables
        self.execute("/root/update.sh")
        # add an initial sysop user as specified
        self.execute("/root/addSysopUser.sh")
            
    def installExtensions(self):
        '''
        install all extensions
        '''
        self.execute("/root/installExtensions.sh")
        # update again to fix potential semantic mediawiki issues
        self.execute("/root/update.sh")
        
    def startUp(self):
        '''
        run startUp scripts
        '''
        self.execute("/root/addCronTabEntry.sh")
            
    def createWikiUser(self,wikiId:str=None,store:bool=False):
        '''
        create my wikiUser and optionally save it
        
        Args:
           store(bool): if True save my user data to the relevant ini File
        '''
        if not wikiId:
            wikiId=f"{self.config.container_base_name}"
        userDict={
            "wikiId":f"{wikiId}",
            "url": f"{self.config.base_url}:{self.config.port}",
            "scriptPath": f"{self.config.script_path}",
            "user": f"{self.config.user}",
            "email":"noreply@nouser.com",
            "version": f"{self.config.fullVersion}",
            "password": f"{self.config.password}"
        }
        wikiUser=WikiUser.ofDict(userDict,encrypted=False)
        if store:
            wikiUser.save()
        return wikiUser
    
    def execute(self,command_str:str):
        '''
        execute the given command string
        
        Args:
            command_str: str - a command string to be executed ...
        '''
        if self.mwContainer:
            if self.config.verbose:
                print(f"Executing docker command {command_str}")
            docker.execute(container=self.mwContainer.container,command=[command_str])
        else:
            mwContainerNameDash=self.getContainerName("mw", "-")
            mwContainerNameUnderscore=self.getContainerName("mw", "_")
            errMsg=f"no mediawiki Container {mwContainerNameDash} or {mwContainerNameUnderscore} for {self.name} activated by docker compose\n- you might want to check the separator character used for container names for your platform {platform.system()}"
            raise Exception(f"{errMsg}")
    
    def close(self):
        """
        close the database
        """
        self.dbClose()
    
    def sqlQuery(self,query):
        """
        run the given SQL query
        """
        if self.dbConn and self.dbConn.is_connected():
            cursor = self.dbConn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            cursor.close()
            return rows
        else:
            if self.config.verbose:
                print (f"Connection to {self.database} on {self.config.host} with user {self.dbUser} not established" )
            return None
        
    def dbClose(self):
        """
        close the database connection
        """
        if self.dbConn and self.dbConn.is_connected():
            self.dbConn.close()
        
    def dbConnect(self,timeout:int=10):
        """
        connect to the database and return the connection
        
        Args:
            timeout(int): number of seconds for timeout
            
        Returns:
            the connection
        """
        if self.dbConn is None:
            try:
                self.dbConn = mysql.connector.connect(host=self.config.host,
                                 database=self.database,
                                 user=self.dbUser,
                                 port=self.config.sqlPort,
                                 password=self.config.mySQLPassword,
                                 connection_timeout=timeout)
        
            except Error as e :
                errMsg=str(e)
                print (f"Connection to {self.database} on {self.config.host} with user {self.dbUser} failed error: {errMsg}" )
                if "Access denied" in errMsg:
                    raise e
        return self.dbConn
    
    def doCheckDBConnection(self,dbStatus:DBStatus,timeout:int=10):
        """
        check the database connection of this application
        
        Args:
            timeout(int): how many seconds to wait
            
        Returns:
            DBStatus
        """          
        dbStatus.attempts+=1
        self.dbConnect(timeout=timeout)
        if self.dbConn and self.dbConn.is_connected():
            rows=self.sqlQuery("select database();")
            dbStatus.ok=True
            if self.config.verbose:
                print (f"{dbStatus.msg} established database returns: {rows[0]}")     
    
    def checkDBConnection(self,timeout:float=10,initialSleep:float=2.5,maxTries:int=7)->DBStatus:
        """
        check database connection with retries
        
        Args:
            timeout(float): number of seconds for timeout
            initialSleep(float): number of seconds to initially wait/sleep
            maxTries(int): maximum number of retries before giving up between each try a sleep is done that starts
            with 0.5 secs and doubles on every retry
            
        Returns:
            dbStatus: the status
        """ 
        conn_msg=f"SQL-Connection to {self.database} on {self.config.host} port {self.config.sqlPort} with user {self.dbUser}"
        dbStatus=DBStatus(attempts=0,ok=False,msg=conn_msg,max_tries=maxTries)
        if self.config.debug:
            print (f"Trying {dbStatus.msg} with max {maxTries} tries and {timeout}s timeout per try - initial sleep {initialSleep}s")
        time.sleep(initialSleep)
        sleep=0.5
        while not dbStatus.ok and dbStatus.attempts<=maxTries:
            try:
                self.doCheckDBConnection(dbStatus,timeout=timeout)
                if not dbStatus.ok:
                    if self.config.verbose:
                        print(f"Connection attempt #{dbStatus.attempts}/{dbStatus.max_tries} failed will retry in {sleep} secs" )   
                    # wait before trying
                    time.sleep(sleep)
                    sleep=sleep*2
            except Exception as ex:
                dbStatus.ex=ex
                if self.config.verbose:
                    print(f"Connection attempt #{dbStatus.attempts} failed with exception {str(ex)} - will not retry ...")
                if self.config.debug:
                    print(traceback.format_exc())
                break
        return dbStatus
    
    def optionalWrite(self,targetPath:str,content:str,overwrite:bool=False):
        """
        optionally Write the modified content to the given targetPath
        
        Args:
            targetPath(str): the path to write the content to
            content(str): the content to write
            overwrite(bool): if True overwrite the existing content
        """
        if not overwrite and os.path.isfile(targetPath):
            if self.config.verbose:
                print(f"{targetPath} already exists!")
            return
        with open(targetPath, "w") as targetFile:
                targetFile.write(content)
    
    def generate(self,templateName:str,targetPath:str,overwrite:bool=False,**kwArgs):
        '''
        generate file at targetPath using the given templateName
        
        Args:
            templateName(str): the Jinja2 template to use
            targetPath(str): the path to the target file
            overwrite(bool): if True overwrite existing files
            kwArgs(): generic keyword arguments to pass on to template rendering
        '''
        try:
            template = self.env.get_template(templateName)
            timestamp=datetime.datetime.now().isoformat()
            content=template.render(mwVersion=self.config.version,mariaDBVersion=self.config.mariaDBVersion,port=self.config.port,sqlPort=self.config.sqlPort,smwVersion=self.config.smwVersion,timestamp=timestamp,**kwArgs)
            self.optionalWrite(targetPath, content, overwrite)

        except TemplateNotFound:
            print(f"no template {templateName} for {self.config.name} {self.config.version}")     
    
    def getComposerRequire(self):
        '''
        get the json string for the composer require e.g. composer.local.json
        '''
        requires=[]
        for ext in self.config.extensionMap.values():
            if hasattr(ext,"composer"):
                # get the composer statement
                composer=ext.composer
                requires.append(composer)
        indent="     "
        delim="" if len(requires)==0 else ",\n"
        requireList=""
        if self.config.smwVersion:
            requireList+=f'{indent}"mediawiki/semantic-media-wiki": "~{self.config.smwVersion}"{delim}'
        for i,require in enumerate(requires):
            delim="" if i>=len(requires)-1 else ",\n"
            requireList+=f"{indent}{require}{delim}"
        requireJson=f"""{{   
  "require": {{
{requireList} 
  }} 
}}"""
        return requireJson
        
    def genComposerRequire(self,composerFilePath,overwrite:bool=False):
        '''
        gen the composer.local.json require file
        
        Args:
            composerFilePath(str): the name of the file to generate
        '''
        requireJson=self.getComposerRequire()
        self.optionalWrite(composerFilePath, requireJson, overwrite)
             
    def generateAll(self,overwrite:bool=False):
        '''
        generate all files needed for the docker handling
        
        Args:
            overwrite(bool): if True overwrite the existing files
        '''
        self.generate("mwDockerfile",f"{self.dockerPath}/Dockerfile",composerVersion=self.composerVersion,overwrite=overwrite)
        self.generate("mwCompose.yml",f"{self.dockerPath}/docker-compose.yml",mySQLRootPassword=self.config.mySQLRootPassword,mySQLPassword=self.config.mySQLPassword,container_base_name=self.config.container_base_name,overwrite=overwrite)
        self.generate(f"mwLocalSettings{self.config.shortVersion}.php",f"{self.dockerPath}/LocalSettings.php",mySQLPassword=self.config.mySQLPassword,hostname=self.config.host,extensions=self.config.extensionMap.values(),mwShortVersion=self.config.shortVersion,logo=self.config.logo,overwrite=overwrite)
        self.generate(f"mwWiki{self.config.shortVersion}.sql",f"{self.dockerPath}/wiki.sql",overwrite=overwrite)
        self.generate(f"addSysopUser.sh",f"{self.dockerPath}/addSysopUser.sh",user=self.config.user,password=self.config.password,overwrite=overwrite)
        self.generate(f"installExtensions.sh",f"{self.dockerPath}/installExtensions.sh",extensions=self.config.extensionMap.values(),branch=self.branch,overwrite=overwrite)
        self.genComposerRequire(f"{self.dockerPath}/composer.local.json",overwrite=overwrite)
        for fileName in ["addCronTabEntry.sh","startRunJobs.sh","initdb.sh","update.sh","phpinfo.php","upload.ini","lang.sh","plantuml.sh"]:
            self.generate(f"{fileName}",f"{self.dockerPath}/{fileName}",overwrite=overwrite)
        
    def down(self,forceRebuild:bool=False):
        """
        run docker compose down
        
        see https://docs.docker.com/engine/reference/commandline/compose_down/
        and https://gabrieldemarmiesse.github.io/python-on-whales/sub-commands/compose/#down
        
        """
        DockerApplication.checkDockerEnvironment(self.config.debug) 
        # change directory so that docker CLI will find the relevant dockerfile and docker-compose.yml
        if self.config.verbose:
            print(f"running docker compose down for {self.config.container_base_name} {self.config.version} docker application ...")
        # remember current directory 
        cwd = os.getcwd()    
        os.chdir(self.dockerPath)
        docker.compose.down(volumes=forceRebuild) 
        # switch back to previous current directory
        os.chdir(cwd)
        
    def up(self,forceRebuild:bool=False):
        """
        start this docker application
        
        Args: 
            forceRebuild(bool): if true stop and remove the existing containers
        """     
        DockerApplication.checkDockerEnvironment(self.config.debug)       
        if self.config.verbose:
            print(f"starting {self.config.container_base_name} {self.config.version} docker application ...")
        if forceRebuild:
            for docker_container in [self.dbContainer,self.mwContainer]:
                if docker_container is not None:
                    container=docker_container.container
                    try:
                        container_name=container.name
                        if self.config.verbose:
                            print(f"stopping and removing container {container_name}")
                    except Exception as container_ex:
                        container=None
                    if container:
                        try:
                            container.stop()
                        except Exception as stop_ex:
                            if self.config.verbose:
                                print(f"stop failed with {str(stop_ex)}")
                            pass
                        try:
                            container.remove()
                        except Exception as remove_ex:
                            if self.config.verbose:
                                print(f"removed failed with {str(remove_ex)}")
                            pass
                    pass

        # remember current directory 
        cwd = os.getcwd()    
     
        # change directory so that docker CLI will find the relevant dockerfile and docker-compose.yml
        os.chdir(self.dockerPath)
        #project_config = docker.compose.config()
        if forceRebuild:
            docker.compose.build()
        # run docker compose up
        # this might take a while e.g. downloading
        # run docker compose up
        docker.compose.up(detach=True,force_recreate=forceRebuild)      
        # switch back to previous current directory
        os.chdir(cwd)
    
        return self.getContainers()
        
    def start(self,forceRebuild:bool=False,withInitDB=True):
        """
        start my containers
        
        Args:
            forceRebuild(bool): if True force rebuilding
            withInitDB(bool): if True intialize my database
        """         
        self.up(forceRebuild=forceRebuild) 
        if withInitDB:
            if self.config.verbose:
                print("Initializing MediaWiki SQL tables")
            dbStatus=self.checkDBConnection()
            if dbStatus.ok:
                # first install extensions
                self.installExtensions()
                # then create and fill database and update it
                self.initDB()
                # then run startUp scripts
                self.startUp()