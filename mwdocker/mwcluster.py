'''
Created on 2021-08-06
@author: wf
'''
from mwdocker.docker import DockerApplication
from mwdocker.mw import ExtensionList
import sys
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter
from mwdocker.logger import Logger

class MediaWikiCluster(object):
    '''
    a cluster of mediawiki docker Applications
    '''
    # https://hub.docker.com/_/mediawiki
    # 2023-01-13
    # MediaWiki Extensions and Skins Security Release Supplement (1.35.9/1.38.4/1.39.1)
    # 2023-02-23 1.39.2 released
    # 2023-04-04 1.39.3 upgrade
    defaultVersions=["1.27.7","1.31.16","1.35.10","1.37.6","1.38.6","1.39.3"]
    defaultExtensionNameList=["Admin Links","Header Tabs","SyntaxHighlight","Variables"]
    defaultUser="Sysop"
    defaultPassword="sysop-1234!"
    defaultLogo="$wgResourceBasePath/resources/assets/wiki.png"

    def __init__(self,versions:list,user:str=None,password:str=None,container_name:str=None,extensionNameList:list=None,extensionJsonFile:str=None,wikiIdList:list=None,sqlPort:int=9306,basePort:int=9080,networkName="mwNetwork",mariaDBVersion="10.11",smwVersion=None,mySQLRootPassword=None,logo=None,debug=False,verbose=True):
        '''
        Constructor
        
        Args:
            versions(list): the list of MediaWiki versions to create docker applications for
            user(str): the initial sysop user to create
            password(str): the initial sysop password to user
            container_name(str): the container name to be used (for a single version)
            extensionNameList(list): a list of names of extensions to be installed
            extensonJsonFile(str): name of an additional jsonFile to load extensions from
            wikiIdList(list): a list of wikiIds to be used to create corresponding wikiUsers for simplified access to the wiki
            sqlPort(int): the base port to be used for  publishing the SQL port (3306) for the docker applications
            basePort(int): the base port to be used for publishing the HTML port (80) for the docker applications
            networkName(str): the name to use for the docker network to be shared by the cluster participants
            mariaDBVersion(str): the Maria DB version to install as the SQL database provider for the docker applications
            smwVersion(str): Semantic MediaWiki Version to be used (if any)
            mySQLRootPassword(str): the mySQL root password to use for the database containers - if None a random password is generated
            logo(str): URL of the logo to be used
            debug(bool): if True debugging is enabled
        '''
        self.debug=debug
        self.verbose=verbose
        if user is None:
            user=MediaWikiCluster.defaultUser
        self.user=user
        if password is None:
            password=MediaWikiCluster.defaultPassword
        if extensionNameList is None:
            extensionNameList=MediaWikiCluster.defaultExtensionNameList
        self.extensionNameList=extensionNameList
        self.extensionJsonFile=extensionJsonFile
        self.wikiIdList=wikiIdList
        if wikiIdList is not None and len(versions)!=len(wikiIdList):
            raise Exception(f"versionList and wikiIdList must have the same length but versions={versions} and wikiIdList={wikiIdList}")
        self.password=password
        self.baseSqlPort=sqlPort
        self.basePort=basePort
        self.versions=versions
        if container_name is not None and len(self.versions)>1:
            print(f"container name {container_name} supplied with multiple versions - ignoring", file=sys.stderr)
            container_name=None
        self.container_name=container_name
        self.mariaDBVersion=mariaDBVersion
        self.smwVersion=smwVersion
        self.mySQLRootPassword=mySQLRootPassword
        # create a network
        self.networkName=networkName
        self.logo=logo
        self.apps={}
         
    @staticmethod
    def getExtensionMap(extensionNameList:list=None,extensionJsonFile:str=None):
        '''
        get map of extensions to handle
        
        Args:
            extensionJsonFile(str): the name of an extra extensionJsonFile (if any)
        '''
        extensionMap={}
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
                    extensionMap[extensionName]=extByName[extensionName]
        return extensionMap
  
    def createApps(self):
        '''
        create my apps
        '''
        self.extensionMap=self.getExtensionMap(self.extensionNameList,self.extensionJsonFile)     
        for i,version in enumerate(self.versions):
            mwApp=self.getDockerApplication(i,version)
            mwApp.generateAll()
            self.apps[version]=mwApp    
        
    def checkDocker(self)->int: 
        """
        check the Docker environment
        
        print an error message on stderr if check fails
        
        Returns:
            int: exitCode - 0 if ok 1 if failed
        
        """
        errMsg=DockerApplication.check()
        if errMsg is not None:
            print(errMsg,file=sys.stderr)
            return 1
        return 0
                
    def start(self,forceRebuild:bool=False,withInitDB=True)->int:
        """
        create and start the composer applications
        
        Returns:
            int: exitCode - 0 if ok 1 if failed
        """         
        exitCode=self.checkDocker()  
        if exitCode>0: return exitCode
        
        for version in self.versions:
            mwApp=self.apps[version]
            mwApp.up(forceRebuild=forceRebuild) 
            if withInitDB:
                if self.verbose:
                    print("Initializing MediaWiki SQL tables")
                dbStatus=mwApp.checkDBConnection()
                if dbStatus.ok:
                    # first install extensions
                    mwApp.installExtensions()
                    # then create and fill database and update it
                    mwApp.initDB()
                    # then run startUp scripts
                    mwApp.startUp()
                    
        return 0
        
    def check(self)->int:
        """
        check the composer applications
        
        Returns:
            int: exitCode - 0 if ok 1 if failed
        """         
        exitCode=self.checkDocker()  
        if exitCode>0: return exitCode
        
        for i,version in enumerate(self.versions):
            mwApp=self.apps[version]
            msg=f"{i}:checking {version} ..."
            print(msg)
            mw,db=mwApp.getContainers()
            if  mw and db and mw.check() and db.check():
                pb_dict=mw.container.host_config.port_bindings
                p80="80/tcp"
                if p80 in pb_dict:
                    pb=pb_dict[p80][0]
                    host_port=pb.host_port
                    Logger.check_and_log_equal(f"port binding",host_port,"expected  port",str(mwApp.port))
                    version_url=f"{mwApp.url}/index.php/Special:Version".replace(str(mwApp.port),host_port)
                    ok=mwApp.checkWiki(version_url)
                    if not ok:
                        exitCode=1
                else:
                    self.log(f"port binding {p80} missing",False)
                    exitCode=1
                pass
        return exitCode
            
    def close(self):
        """
        close my apps
        """
        for mwApp in self.apps.values():
            mwApp.close()
            
    def getDockerApplication(self,i,version):
        '''
        get the docker application for the given version index and version
        
        Args:
            i(int): the index of the version
            version(str): the mediawiki version to use
        
        Returns:
            DockerApplication: the docker application
        '''
        port=self.basePort+i
        sqlPort=self.baseSqlPort+i
        wikiId=None
        if self.wikiIdList is not None:
            wikiId=self.wikiIdList[i]                        
        mwApp=DockerApplication(user=self.user,password=self.password,version=version,container_name=self.container_name,extensionMap=self.extensionMap,wikiId=wikiId,mariaDBVersion=self.mariaDBVersion,smwVersion=self.smwVersion,port=port,sqlPort=sqlPort,mySQLRootPassword=self.mySQLRootPassword,logo=self.logo,debug=self.debug)
        return mwApp

__version__ = "0.7.0"
__date__ = '2021-06-21'
__updated__ = '2023-01-25'
DEBUG=False

def main(argv=None): # IGNORE:C0111
    '''main program.'''

    if argv is None:
        argv = sys.argv[1:]

    program_name = "mwcluster"
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = "mwcluster"
    user_name="Wolfgang Fahl"

    program_license = '''%s

  Created by %s on %s.
  Copyright 2021-2022 Wolfgang Fahl. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

''' % (program_shortdesc,user_name, str(__date__))
    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=ArgumentDefaultsHelpFormatter)
        parser.add_argument('-bp', '--basePort',dest='basePort',type=int,default=9080,help="set how base html port 80 to be exposed - incrementing by one for each version [default: %(default)s]")
        parser.add_argument('-c','--check',action="store_true",default=False,help="check the wikis [default: %(default)s]")
        parser.add_argument('-cn','--container_name',default=None,help="set container name (only valid and recommended for single version call)")
        parser.add_argument("-d", "--debug", dest="debug",   action="store_true", help="set debug level [default: %(default)s]")
        parser.add_argument('-el', '--extensionList', dest='extensionNameList', nargs="*",default=MediaWikiCluster.defaultExtensionNameList,help="list of extensions to be installed [default: %(default)s]")
        parser.add_argument('-ej', '--extensionJson',dest='extensionJsonFile',default=None,help="additional extension descriptions default: None")
        parser.add_argument("-f", "--forceRebuild", dest="forceRebuild",   action="store_true", help="shall the applications rebuild be forced (with stop and remove of existing containers)")
        parser.add_argument("--logo", default=MediaWikiCluster.defaultLogo, help="set Logo [default: %(default)s]")
        parser.add_argument('-mv', '--mariaDBVersion', dest='mariaDBVersion',default="10.9",help="mariaDB Version to be installed [default: %(default)s]")
        parser.add_argument('-p','--password',dest='password',default=MediaWikiCluster.defaultPassword, help="set password for initial user [default: %(default)s] ")
        parser.add_argument('-sp', '--sqlBasePort',dest='sqlPort',type=int,default=9306,help="set base mySql port 3306 to be exposed - incrementing by one for each version [default: %(default)s]")
        parser.add_argument('-smw','--smwVersion',dest='smwVersion',default=None,help="set SemanticMediaWiki Version to be installed default is None - no installation of SMW")
        parser.add_argument('-u','--user',dest='user',default=MediaWikiCluster.defaultUser, help="set username of initial user with sysop rights [default: %(default)s] ")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument('-vl', '--versionList', dest='versions', nargs="*",default=MediaWikiCluster.defaultVersions,help="mediawiki versions to create docker applications for [default: %(default)s] ")
        parser.add_argument('-wl', '--wikiIdList', dest='wikiIdList', nargs="*",default=None,help="list of wikiIDs to be used for for py-3rdparty-mediawiki wikiuser quick access")   
        args = parser.parse_args(argv)
        action="checking docker access" if args.check else "creating docker compose applications"
        print(f"{action} for mediawiki versions {args.versions}")
        # create a MediaWiki Cluster
        mwCluster=MediaWikiCluster(args.versions,user=args.user,password=args.password,container_name=args.container_name,extensionJsonFile=args.extensionJsonFile,extensionNameList=args.extensionNameList,wikiIdList=args.wikiIdList,basePort=args.basePort,sqlPort=args.sqlPort,mariaDBVersion=args.mariaDBVersion,smwVersion=args.smwVersion,logo=args.logo,debug=args.debug)
        mwCluster.createApps()
        if args.check:
            return mwCluster.check()
        else:
            return mwCluster.start(forceRebuild=args.forceRebuild)
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 1
    except Exception as e:
        if DEBUG:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        return 2
            
if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-d")
    sys.exit(main())
    