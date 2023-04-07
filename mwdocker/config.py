'''
Created on 2023-04-06

@author: wf
'''
from dataclasses import dataclass, field
import re
import secrets
import socket
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
    smwVersion:str=None
    extensionNameList:Optional[List[str]]=field(default_factory=lambda: ["Admin Links","Header Tabs","SyntaxHighlight","Variables"])
    extensionJsonFile:str=None
    user:str="Sysop"
    prefix:str="mw"
    password_length:int = 15
    password:str="sysop-1234!"
    mySQLRootPassword:str=None
    mySQLPassword:str=None
    logo:str="$wgResourceBasePath/resources/assets/wiki.png"
    port:int=9080
    sqlPort:int=9306
    prot:str="http"
    host:str=Host.get_default_host()    
    script_path:str=""
    container_base_name:str=None  
    networkName:str="mwNetwork"
    mariaDBVersion:str="10.11"
    forceRebuild:bool=False
    debug:bool=False
    verbose:bool=True
    wikiId:str=None
    
    def __post_init__(self):
        """
        post initialization configuration
        """
        self.fullVersion=f"MediaWiki {self.version}"
        self.underscoreVersion=self.version.replace(".","_")
        self.shortVersion=self.getShortVersion()
        self.base_url=f"{self.prot}://{self.host}"
        self.url=f"{self.base_url}{self.script_path}:{self.port}"
        if not self.container_base_name:
            self.container_base_name=f"{self.prefix}-{self.shortVersion}"
        
    def getShortVersion(self,separator=""):
        '''
        get my short version e.g. convert 1.27.7 to 127
        
        Returns:
            str: the short version string
        '''
        versionMatch=re.match("(?P<major>[0-9]+)\.(?P<minor>[0-9]+)",self.version)
        shortVersion=f"{versionMatch.group('major')}{separator}{versionMatch.group('minor')}"
        return shortVersion
    
    def random_password(self,length:int = 15)->str:
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
        extByName,duplicates=extensionList.getLookup("name")
        if len(duplicates)>0:
            print(f"{len(duplicates)} duplicate extensions: ")
            for duplicate in duplicates:
                print(duplicate.name)
        if extensionNameList is not None:
            for extensionName in extensionNameList:
                if extensionName in extByName:
                    self.extensionMap[extensionName]=extByName[extensionName]
        pass            
        
    def fromArgs(self,args):
        """
        initialize me from the given commmand line arguments
        
        Args:
            args(Namespace): the command line arguments
        """
        self.host=args.host
        self.prot=args.prot
        self.script_path=args.script_path
        self.versions=args.versions
        self.user=args.user
        self.password=args.password
        self.container_base_name=args.container_name
        self.extensionJsonFile=args.extensionJsonFile
        self.extensionNameList=args.extensionNameList
        self.basePort=args.basePort
        self.sqlPort=args.sqlPort
        self.mariaDBVersion=args.mariaDBVersion
        self.smwVersion=args.smwVersion
        self.logo=args.logo
        self.verbose=not args.quiet
        self.debug=args.debug
        # passwords
        self.mySQLRootPassword=args.mysqlPassword
        if not self.mySQLRootPassword:
            self.mySQLRootPassword=self.random_password(self.password_length)
        self.mySQLPassword=self.random_password(self.password_length)    
        self.getExtensionMap(self.extensionNameList, self.extensionJsonFile)
   
    def addArgs(self,parser):
        """
        add Arguments to the given parser
        """
        parser.add_argument('-cn','--container_name',default=self.container_base_name,help="set container name (only valid and recommended for single version call)")
        parser.add_argument("-d", "--debug", dest="debug",   action="store_true", help="set debug level [default: %(default)s]")
        parser.add_argument('-el', '--extensionList', dest='extensionNameList', nargs="*",default=self.extensionNameList,help="list of extensions to be installed [default: %(default)s]")
        parser.add_argument('-ej', '--extensionJson',dest='extensionJsonFile',default=self.extensionJsonFile,help="additional extension descriptions default: [default: %(default)s]")
        parser.add_argument("--host", default=Host.get_default_host(),
                            help="the host to serve / listen from [default: %(default)s]")
        parser.add_argument("--logo", default=self.logo, help="set Logo [default: %(default)s]")
        parser.add_argument('-mv', '--mariaDBVersion', dest='mariaDBVersion',default=self.mariaDBVersion,help="mariaDB Version to be installed [default: %(default)s]")
        parser.add_argument('--mysqlPassword',default=self.mySQLRootPassword, help="set sqlRootPassword [default: %(default)s] - random password if None")
        parser.add_argument('-p','--password',dest='password',default=self.password, help="set password for initial user [default: %(default)s] ")
        parser.add_argument('-pl','--passwordLength',default=self.password_length, help="set the password length for random passwords[default: %(default)s] ")
        parser.add_argument("--prefix",default=self.prefix,help="the container name prefix to use [default: %(default)s]")
        parser.add_argument("--prot",default=self.prot,help="change to https in case [default: %(default)s]")
        parser.add_argument("--script_path",default=self.script_path,help="change to any script_path you might need to set [default: %(default)s]")
        parser.add_argument('-sp', '--sqlBasePort',dest='sqlPort',type=int,default=self.sqlPort,help="set base mySql port 3306 to be exposed - incrementing by one for each version [default: %(default)s]")
        parser.add_argument('-smw','--smwVersion',dest='smwVersion',default=self.smwVersion,help="set SemanticMediaWiki Version to be installed default is None - no installation of SMW")
        parser.add_argument('-u','--user',dest='user',default=self.user, help="set username of initial user with sysop rights [default: %(default)s] ")
        parser.add_argument('-q', '--quiet', help="not verbose [default: %(default)s]",action="store_true")

@dataclass
class MwClusterConfig(MwConfig):
    """
    MediaWiki Cluster configuration for multiple wikis
    """
    versions:Optional[List[str]]=field(default_factory=lambda: ["1.27.7","1.31.16","1.35.10","1.37.6","1.38.6","1.39.3"])
    basePort:int=9080
    
    def addArgs(self,parser):
        """
        add my arguments to the given parser
        """
        super().addArgs(parser) 
        parser.add_argument('-bp', '--basePort',dest='basePort',type=int,default=self.basePort,help="set how base html port 80 to be exposed - incrementing by one for each version [default: %(default)s]")
        parser.add_argument('-vl', '--versionList', dest='versions', nargs="*",default=self.versions,help="mediawiki versions to create docker applications for [default: %(default)s] ")    