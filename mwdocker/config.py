'''
Created on 2023-04-06

@author: wf
'''
import dataclasses
import dacite
from dataclasses import dataclass, field
from pathlib import Path
import json
import os
import re
import secrets
import socket
from urllib.parse import urlparse
from typing import Optional, List
from mwdocker.mw import ExtensionList

class Host:
    """
    Host name getter
    """
    @classmethod    
    def get_default_host(cls) -> str:
        """
        get the default host as the fully qualifying hostname
        of the computer the server runs on
        
        Returns:
            str: the hostname
        """
        host = socket.getfqdn()
        # work around https://github.com/python/cpython/issues/79345
        if host == "1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.ip6.arpa":
            host = "localhost"  # host="127.0.0.1"
        return host
        
@dataclass
class MwConfig:
    """
    MediaWiki configuration for a Single Wiki
    """
    version:str="1.39.3"
    smw_version:Optional[str]=None
    extensionNameList:Optional[List[str]]=field(default_factory=lambda: ["Admin Links","Header Tabs","SyntaxHighlight","Variables"])
    extensionJsonFile:Optional[str]=None
    user:str="Sysop"
    prefix:str="mw"
    password_length:int = 15
    random_password:bool=False
    force_user:bool=False
    password:str="sysop-1234!"
    mySQLRootPassword:Optional[str]=None
    mySQLPassword:Optional[str]=None
    logo:str="$wgResourceBasePath/resources/assets/wiki.png"
    port:int=9080
    sql_port:int=9306
    url=None
    full_url=None
    prot:str="http"
    host:str=Host.get_default_host()    
    script_path:str=""
    container_base_name:str=None  
    networkName:str="mwNetwork"
    mariaDBVersion:str="10.11"
    forceRebuild:bool=False
    debug:bool=False
    verbose:bool=True
    wikiId:Optional[str]=None
    docker_path:Optional[str]=None
    
    def default_docker_path(self)->str:
        """
        get the default docker path
        
        Returns:
            str: $HOME/.pymediawikidocker
        """
        home = str(Path.home())
        docker_path=f'{home}/.pymediawikidocker' 
        return docker_path
    
    def __post_init__(self):
        """
        post initialization configuration
        """
        self.fullVersion=f"MediaWiki {self.version}"
        self.underscoreVersion=self.version.replace(".","_")
        self.shortVersion=self.getShortVersion()
        if not self.docker_path:
            self.docker_path=self.default_docker_path()
        if not self.container_base_name:
            self.container_base_name=f"{self.prefix}-{self.shortVersion}"
        self.reset_url(self.url)
            
    def reset_url(self,url:str):     
        """
        reset my url
        
        Args:
            url(str): the url to set
        """  
        if url:
            pr=urlparse(url)
            self.prot=pr.scheme
            self.host=pr.hostname
            self.script_path=pr.path
            self.base_url=f"{self.prot}://{self.host}"
            self.full_url=url
        else:
            self.base_url=f"{self.prot}://{self.host}"
            self.full_url=f"{self.base_url}{self.script_path}:{self.port}"
          
    def reset_container_base_name(self,container_base_name:str=None):
        """
        reset the container base name to the given name
        
        Args:
            container_base_name(str): the new container base name
        """
        self.container_base_name=container_base_name
        self.__post_init__()
          
    def as_dict(self)->dict:
        """
        return my fields as a dict
        dataclasses to dict conversion convenienc and information hiding
        
        Returns:
            dict: my fields in dict format
        """
        config_dict=dataclasses.asdict(self)
        return config_dict
    
    def as_json(self)->str:
        """
        return me as a json string
        
        Returns:
            str: my json representation
        """
        config_dict=self.as_dict()
        json_str=json.dumps(config_dict,indent=2)
        return json_str
    
    def get_config_path(self)->str:
        """
        get my configuration base path
        
        Returns:
            str: the path to my configuration
        """
        config_base_path=f"{self.docker_path}/{self.container_base_name}"
        os.makedirs(config_base_path, exist_ok=True)
        path=f"{config_base_path}/MwConfig.json"
        return path
    
    def save(self,path:str=None)->str:
        """
        save my json
        
        Args:
            path(str): the path to store to - if None use {docker_path}/{container_base_name}/MwConfig.json
        Returns:
            str: the path 
        """
        if path is None:
            path=self.get_config_path()
        
        json_str=self.as_json()
        print(json_str,  file=open(path, 'w'))
        return path
    
    def load(self,path:str=None)->"MwConfig":
        """
        load the the MwConfig from the given path of if path is None (default)
        use the config_path for the current configuration
        
        restores the ExtensionMap on load
        
        Args:
            path(str): the path to load from
            
        Returns:
            MwConfig: a MediaWiki Configuration
        """
        if path is None:
            path=self.get_config_path()
        with open(path, 'r') as json_file:
            json_str = json_file.read()
            config_dict=json.loads(json_str)
            config=dacite.from_dict(data_class=self.__class__ ,data=config_dict)
            # restore extension map
            config.getExtensionMap(config.extensionNameList, config.extensionJsonFile)
            return config
        
    def getShortVersion(self,separator=""):
        '''
        get my short version e.g. convert 1.27.7 to 127
        
        Returns:
            str: the short version string
        '''
        versionMatch=re.match("(?P<major>[0-9]+)\.(?P<minor>[0-9]+)",self.version)
        shortVersion=f"{versionMatch.group('major')}{separator}{versionMatch.group('minor')}"
        return shortVersion
    
    def create_random_password(self,length:int = 15)->str:
        """
        create a random password

        Args:
            length(int): the length of the password

        Returns:
            str:a random password with the given length
        """
        return secrets.token_urlsafe(length)
    
    def getWikiId(self):
        """
        get the wikiId
        
        Returns:
            str: e.g. mw-9080
        """
        if self.wikiId is None:
            wikiId=f"{self.prefix}-{self.port}"
        else:
            wikiId=self.wikiId
        return wikiId
    
    def getExtensionMap(self,extensionNameList:list=None,extensionJsonFile:str=None):
        '''
        get map of extensions to handle
        
        Args:
            extensionNameList(list): a lit of extension names
            extensionJsonFile(str): the name of an extra extensionJsonFile (if any)
        '''
        self.extensionMap={}
        extensionList=ExtensionList.restore()
        if extensionJsonFile is not None:
            extraExtensionList=ExtensionList()
            extraExtensionList.restoreFromJsonFile(extensionJsonFile.replace(".json",""))
            for ext in extraExtensionList.extensions:
                extensionList.extensions.append(ext)
        self.extByName,duplicates=extensionList.getLookup("name")
        if len(duplicates)>0:
            print(f"{len(duplicates)} duplicate extensions: ")
            for duplicate in duplicates:
                print(duplicate.name)
        if extensionNameList is not None:
            self.addExtensions(extensionNameList)
        return self.extensionMap          
    
    def addExtensions(self,extensionNameList):
        """
        add extensions for the given list of extension names
        """
        for extensionName in extensionNameList:
            if extensionName in self.extByName:
                self.extensionMap[extensionName]=self.extByName[extensionName]
            else:
                print(f"warning: extension {extensionName} not known")
        
    def fromArgs(self,args):
        """
        initialize me from the given commmand line arguments
        
        Args:
            args(Namespace): the command line arguments
        """
        self.prefix=args.prefix
        self.container_base_name=args.container_name
        self.docker_path=args.docker_path
        self.extensionNameList=args.extensionNameList
        self.extensionJsonFile=args.extensionJsonFile
        self.forceRebuild=args.forceRebuild
        self.host=args.host
        self.logo=args.logo
        self.mariaDBVersion=args.mariaDBVersion
        # passwords
        self.mySQLRootPassword=args.mysqlPassword
        if not self.mySQLRootPassword:
            self.mySQLRootPassword=self.create_random_password(self.password_length)
        self.mySQLPassword=self.create_random_password(self.password_length)    
        self.prot=args.prot
        self.script_path=args.script_path
        self.versions=args.versions
        self.user=args.user
        self.random_password=args.random_password
        self.force_user=args.force_user
        self.password=args.password
        self.password_length=args.password_length
        self.base_port=args.base_port
        self.sql_port=args.sql_port
        self.smw_version=args.smw_version
        self.verbose=not args.quiet
        self.debug=args.debug
        self.getExtensionMap(self.extensionNameList, self.extensionJsonFile)
        self.reset_url(args.url)
   
    def addArgs(self,parser):
        """
        add Arguments to the given parser
        """
        parser.add_argument('-cn','--container_name',default=self.container_base_name,help="set container name (only valid and recommended for single version call)")
        parser.add_argument("-d", "--debug", dest="debug",   action="store_true", default=self.debug, help="enable debug mode [default: %(default)s]")
        parser.add_argument('-el', '--extensionList', dest='extensionNameList', nargs="*",default=self.extensionNameList,help="list of extensions to be installed [default: %(default)s]")
        parser.add_argument('-ej', '--extensionJson',dest='extensionJsonFile',default=self.extensionJsonFile,help="additional extension descriptions default: [default: %(default)s]")
        parser.add_argument("-f", "--forceRebuild", action="store_true", default=self.forceRebuild,help="force rebuilding  [default: %(default)s]")
        parser.add_argument("-fu","--force_user",action="store_true",default=self.force_user,help="force overwrite of wikiuser")
        parser.add_argument("--host", default=Host.get_default_host(),
                            help="the host to serve / listen from [default: %(default)s]")
        parser.add_argument("-dp","--docker_path", default=self.default_docker_path(),
                            help="the base directory to store docker and jinja template files [default: %(default)s]")
        parser.add_argument("--logo", default=self.logo, help="set Logo [default: %(default)s]")
        parser.add_argument('-mv', '--mariaDBVersion', dest='mariaDBVersion',default=self.mariaDBVersion,help="mariaDB Version to be installed [default: %(default)s]")
        parser.add_argument('--mysqlPassword',default=self.mySQLRootPassword, help="set sqlRootPassword [default: %(default)s] - random password if None")
        parser.add_argument("-rp", "--random_password", action="store_true", default=self.random_password, help="create random password and create wikiuser while at it")
        parser.add_argument('-p','--password',dest='password',default=self.password, help="set password for initial user [default: %(default)s] ")
        parser.add_argument('-pl','--password_length',default=self.password_length, help="set the password length for random passwords[default: %(default)s] ")
        parser.add_argument("--prefix",default=self.prefix,help="the container name prefix to use [default: %(default)s]")
        parser.add_argument("--prot",default=self.prot,help="change to https in case [default: %(default)s]")
        parser.add_argument("--script_path",default=self.script_path,help="change to any script_path you might need to set [default: %(default)s]")
        parser.add_argument("--url",default=self.url,help="will set prot host,script_path, and optionally port based on the url given [default: %(default)s]")
        parser.add_argument('-sp', '--sql_base_port',dest='sql_port',type=int,default=self.sql_port,help="set base mySql port 3306 to be exposed - incrementing by one for each version [default: %(default)s]")
        parser.add_argument('-smw','--smw_version',dest='smw_version',default=self.smw_version,help="set SemanticMediaWiki Version to be installed default is None - no installation of SMW")
        parser.add_argument('-u','--user',dest='user',default=self.user, help="set username of initial user with sysop rights [default: %(default)s] ")
        parser.add_argument('-q', '--quiet', default=not self.verbose,help="not verbose [default: %(default)s]",action="store_true")

@dataclass
class MwClusterConfig(MwConfig):
    """
    MediaWiki Cluster configuration for multiple wikis
    """
    versions:Optional[List[str]]=field(default_factory=lambda: ["1.35.10","1.38.6","1.39.3"])
    base_port:int=9080
    
    def addArgs(self,parser):
        """
        add my arguments to the given parser
        """
        super().addArgs(parser) 
        parser.add_argument('-bp', '--base_port',dest='base_port',type=int,default=self.base_port,help="set how base html port 80 to be exposed - incrementing by one for each version [default: %(default)s]")
        parser.add_argument('-vl', '--version_list', dest='versions', nargs="*",default=self.versions,help="mediawiki versions to create docker applications for [default: %(default)s] ")    