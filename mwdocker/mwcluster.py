'''
Created on 2021-08-06
@author: wf
'''
import dataclasses
from mwdocker.docker import DockerApplication
from mwdocker.version import Version
from mwdocker.config import MwClusterConfig
from mwdocker.logger import Logger
import sys
from argparse import ArgumentParser
from argparse import ArgumentDefaultsHelpFormatter
import webbrowser
import traceback

class MediaWikiCluster(object):
    '''
    a cluster of mediawiki docker Applications
    '''
    # https://hub.docker.com/_/mediawiki
    # 2023-01-13
    # MediaWiki Extensions and Skins Security Release Supplement (1.35.9/1.38.4/1.39.1)
    # 2023-02-23 1.39.2 released
    # 2023-04-04 1.39.3 upgrade
    
    def __init__(self,config:MwClusterConfig):
        '''
        Constructor
        
        Args:
            config(MWClusterConfig): the MediaWiki Cluster Configuration to use
        '''
        self.config=config
        self.apps={}       
  
    def createApps(self,withGenerate:bool=True)->dict:
        '''
        create my apps
        
        Args:
            withGenerate(bool): if True generate the config files
            
        Returns:
            dict(str): a dict of apps by version
        '''  
        app_count=len(self.config.versions)
        for i,version in enumerate(self.config.versions):
            mwApp=self.getDockerApplication(i,app_count,version)
            if withGenerate:
                mwApp.generateAll(overwrite=self.config.forceRebuild)     
            self.apps[version]=mwApp    
        return self.apps
        
    def checkDocker(self)->int: 
        """
        check the Docker environment
        
        print an error message on stderr if check fails
        
        Returns:
            int: exitCode - 0 if ok 1 if failed
        
        """
        errMsg=DockerApplication.checkDockerEnvironment(self.config.debug)
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
        
        for version in self.config.versions:
            mwApp=self.apps[version]
            mwApp.start(forceRebuild=forceRebuild,withInitDB=withInitDB)
        return 0
    
    def down(self,forceRebuild:bool=False):
        """
        run docker compose down
        """
        exitCode=self.checkDocker()  
        if exitCode>0: return exitCode
        for _i,version in enumerate(self.config.versions):
            mwApp=self.apps[version]
            mwApp.down(forceRebuild)
    
    def listWikis(self)->int:
        """
        list my wikis
        
        Returns:
            int: exitCode - 0 if ok 1 if failed
        """
        exitCode=self.checkDocker()  
        if exitCode>0: return exitCode
        for i,version in enumerate(self.config.versions):
            mwApp=self.apps[version]
            mw,db=mwApp.getContainers()
            config=mwApp.config
            ok=mw and db
            msg=f"{i+1}:{config.container_base_name} {config.fullVersion}"
            Logger.check_and_log(msg, ok)
        return exitCode
        
    def check(self)->int:
        """
        check the composer applications
        
        Returns:
            int: exitCode - 0 if ok 1 if failed
        """         
        exitCode=self.checkDocker()  
        if exitCode>0: return exitCode
        
        for i,version in enumerate(self.config.versions):
            mwApp=self.apps[version]
            msg=f"{i+1}:checking {version} ..."
            print(msg)
            exitCode=mwApp.check()
        return exitCode
            
    def close(self):
        """
        close my apps
        """
        for mwApp in self.apps.values():
            mwApp.close()
            
    def getDockerApplication(self,i:int,count:int,version:str):
        '''
        get the docker application for the given version index and version
        
        Args:
            i(int): the index of the version
            count(int): total number of Docker applications in this cluster
            version(str): the mediawiki version to use
        
        Returns:
            DockerApplication: the docker application
        '''
        # please note that we are using the subclass MwClusterConfig here although
        # we only need the superclass MwConfig - we let inheritance work here for us but
        # have to ignore the superfluous fields
        appConfig=dataclasses.replace(self.config)
        appConfig.extensionMap=self.config.extensionMap.copy()
        appConfig.version=version
        appConfig.port=self.config.base_port+i
        appConfig.sql_port=self.config.sql_port+i   
        # let post_init create a new container_base_name
        if count>1:
            appConfig.container_base_name=None
        appConfig.__post_init__()            
        mwApp=DockerApplication(config=appConfig)
        return mwApp

DEBUG=False

def main(argv=None): # IGNORE:C0111
    '''main program.'''

    if argv is None:
        argv = sys.argv[1:]

    program_name = "mwcluster"
    program_version = f"v{Version.version}"
    program_build_date = str(Version.updated)
    program_version_message = f'{program_name} ({program_version},{program_build_date})'
    program_license = Version.license
    
    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=ArgumentDefaultsHelpFormatter)
        mwClusterConfig=MwClusterConfig()
        mwClusterConfig.addArgs(parser)
        parser.add_argument("--about", help="show about info [default: %(default)s]", action="store_true")
        parser.add_argument("--create", action="store_true", help="create wikis [default: %(default)s]")
        parser.add_argument("--down", action="store_true", help="shutdown wikis [default: %(default)s]")
        parser.add_argument("--check",action="store_true",help="check the wikis [default: %(default)s]")
        parser.add_argument("--list",action="store_true",help="list the wikis [default: %(default)s]")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        args = parser.parse_args(argv)
        if args.about:
            print(program_version_message)
            print(f"see {Version.doc_url}")
            webbrowser.open(Version.doc_url)
        else:
            action=None
            withGenerate=False
            if args.check: 
                action="checking docker access" 
            elif args.create: 
                action="creating docker compose applications" 
                withGenerate=True
            elif args.list:
                action="listing docker compose wiki applications"
            elif args.down:
                action="running docker compose down"
            if not action:
                parser.print_usage()
            else:
                print(f"{action} for mediawiki versions {args.versions}")
                # create a MediaWiki Cluster
                mwClusterConfig.fromArgs(args)
                mwCluster=MediaWikiCluster(config=mwClusterConfig)
                mwCluster.createApps(withGenerate=withGenerate)
                if args.check:
                    return mwCluster.check()
                elif args.create:
                    return mwCluster.start(forceRebuild=args.forceRebuild)
                elif args.list:
                    return mwCluster.listWikis()
                elif args.down:
                    return mwCluster.down(forceRebuild=args.forceRebuild)
    except KeyboardInterrupt:
        ### handle keyboard interrupt ###
        return 1
    except Exception as e:
        if DEBUG:
            raise(e)
        indent = len(program_name) * " "
        sys.stderr.write(program_name + ": " + repr(e) + "\n")
        sys.stderr.write(indent + "  for help use --help")
        if args is None:
            print("args could not be parsed")
        elif args.debug:
            print(traceback.format_exc())
        return 2
            
if __name__ == "__main__":
    if DEBUG:
        sys.argv.append("-d")
    sys.exit(main())
    