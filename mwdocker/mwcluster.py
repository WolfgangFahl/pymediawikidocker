'''
Created on 2021-08-06
@author: wf
'''
from mwdocker.docker import DockerApplication
import sys
from argparse import ArgumentParser
from argparse import RawDescriptionHelpFormatter

class MediaWikiCluster(object):
    '''
    a cluster of mediawiki docker Applications
    '''
    defaultVersions=["1.27.7","1.31.14","1.35.2","1.36.0"]
    defaultUser="Sysop"
    defaultPassword="sysop-1234!"

    def __init__(self,versions,user:str=None,password:str=None,sqlPort:int=9306,basePort:int=9080,networkName="mwNetwork",mariaDBVersion="10.5",smwVersion=None,mySQLRootPassword=None,debug=False,verbose=True):
        '''
        Constructor
        
        Args:
            versions(list): the list of MediaWiki versions to create docker applications for
            user(str): the initial sysop user to create
            password(str): the initial sysop password to user
            sqlPort(int): the base port to be used for  publishing the SQL port (3306) for the docker applications
            basePort(int): the base port to be used for publishing the HTML port (80) for the docker applications
            networkName(str): the name to use for the docker network to be shared by the cluster participants
            mariaDBVersion(str): the Maria DB version to install as the SQL database provider for the docker applications
            smwVersion(str): Semantic MediaWiki Version to be used (if any)
            mySQLRootPassword(str): the mySQL root password to use for the database containers - if None a random password is generated
            debug(bool): if True debugging is enabled
        '''
        self.debug=debug
        self.verbose=verbose
        if user is None:
            user=MediaWikiCluster.defaultUser
        self.user=user
        if password is None:
            password=MediaWikiCluster.defaultPassword
        self.password=password
        self.baseSqlPort=sqlPort
        self.basePort=basePort
        self.versions=versions
        self.mariaDBVersion=mariaDBVersion
        self.smwVersion=smwVersion
        self.mySQLRootPassword=mySQLRootPassword
        # create a network
        self.networkName=networkName
        self.apps={}
                
    def start(self,forceRebuild:bool=False,withInitDB=True)->int:
        '''
        create and start the composer applications
        
        Returns:
            int: exitCode - 0 if ok 1 if failed
        '''           
        errMsg=DockerApplication.check()
        if errMsg is not None:
            print(errMsg,file=sys.stderr)
            return 1
            
        
        for i,version in enumerate(self.versions):
            mwApp=self.getDockerApplication(i,version)
            mwApp.generateAll()
            mwApp.up(forceRebuild=forceRebuild) 
            self.apps[version]=mwApp     
            if withInitDB:
                if self.verbose:
                    print("Initializing MediaWiki SQL tables")
                if mwApp.checkDBConnection():
                    mwApp.initDB()
        return 0
            
    def close(self):
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
        mwApp=DockerApplication(user=self.user,password=self.password,version=version,debug=True,mariaDBVersion=self.mariaDBVersion,smwVersion=self.smwVersion,port=port,sqlPort=sqlPort,mySQLRootPassword=self.mySQLRootPassword)
        return mwApp
            
    def genDockerFiles(self):
        '''
        generate all docker files
        '''
        for i,version in enumerate(self.versions):
            mwApp=self.getDockerApplication(i,version)
            mwApp.generateAll()

__version__ = "0.0.11"
__date__ = '2021-06-21'
__updated__ = '2021-06-23'
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
  Copyright 2021 Wolfgang Fahl. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

''' % (program_shortdesc,user_name, str(__date__))
    try:
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-d", "--debug", dest="debug",   action="store_true", help="set debug level [default: %(default)s]")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument('-vl', '--versionList', dest='versions', nargs="*",default=MediaWikiCluster.defaultVersions)
        parser.add_argument('-u','--user',dest='user',default=MediaWikiCluster.defaultUser)
        parser.add_argument('-p','--password',dest='password',default=MediaWikiCluster.defaultPassword)
        parser.add_argument('-bp', '--basePort',dest='basePort',type=int,default=9080)
        parser.add_argument('-sp', '--sqlBasePort',dest='sqlPort',type=int,default=9306)
        parser.add_argument('-smw','--smwVersion',dest='smwVersion',default=None)
        parser.add_argument('-mv', '--mariaDBVersion', dest='mariaDBVersion',default="10.5",)
        parser.add_argument("-f", "--forceRebuild", dest="forceRebuild",   action="store_true", help="shall the applications rebuild be forced (with stop and remove of existing containers)")
        args = parser.parse_args(argv)
        print(f"mediawiki versions {args.versions}")
        # create a MediaWiki Cluster
        mwCluster=MediaWikiCluster(args.versions,user=args.user,password=args.password,basePort=args.basePort,sqlPort=args.sqlPort,mariaDBVersion=args.mariaDBVersion,smwVersion=args.smwVersion,debug=args.debug)
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
    