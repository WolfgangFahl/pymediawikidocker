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

    def __init__(self,debug=False,sqlPort=9306,basePort=9080,versions=["1.27.7","1.31.14","1.35.2"],networkName="mwNetwork",mariaDBVersion="10.5",mySQLRootPassword=None):
        '''
        Constructor
        
        Args:
            debug(bool): if True debugging is enabled
            sqlPort(int): the base port to be used for  publishing the SQL port (3306) for the docker applications
            basePort(int): the base port to be used for publishing the HTML port (80) for the docker applications
            versions(list): the list of MediaWiki versions to create docker applications for
            networkName(str): the name to use for the docker network to be shared by the cluster participants
            mariaDBVersion(str): the Maria DB version to install as the SQL database provider for the docker applications
            mySQLRootPassword(str): the mySQL root password to use for the database containers - if None a random password is generated
        '''
        self.debug=debug
        self.baseSqlPort=sqlPort
        self.basePort=basePort
        self.versions=versions
        self.mariaDBVersion=mariaDBVersion
        self.mySQLRootPassword=mySQLRootPassword
        # create a network
        self.networkName=networkName
        self.apps={}
                
    def start(self,forceRebuild:bool=False,withInitDB=True):
        '''
        create and start the composer applications
        '''           
        for i,version in enumerate(self.versions):
            mwApp=self.getDockerApplication(i,version)
            mwApp.generateAll()
            mwApp.up(forceRebuild=forceRebuild) 
            self.apps[version]=mwApp     
            if withInitDB:
                if self.verbose:
                    print("Initializing MediaWiki SQL tables")
                if mwApp.checkDBConnection():
                    mwApp.execute("/tmp/initdb.sh")
            
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
        mwApp=DockerApplication(version=version,debug=True,mariaDBVersion=self.mariaDBVersion,port=port,sqlPort=sqlPort,mySQLRootPassword=self.mySQLRootPassword)
        return mwApp
            
    def genDockerFiles(self):
        '''
        generate all docker files
        '''
        for i,version in enumerate(self.versions):
            mwApp=self.getDockerApplication(i,version)
            mwApp.generateAll()

__version__ = "0.0.1"
__date__ = '2021-06-21'
__updated__ = '2021-06-21'
DEBUG=False

def main(argv=None): # IGNORE:C0111
    '''main program.'''

    if argv is None:
        argv = sys.argv[1:]

    program_name = "mwcluster"
    program_version = "v%s" % __version__
    program_build_date = str(__updated__)
    program_version_message = '%%(prog)s %s (%s)' % (program_version, program_build_date)
    program_shortdesc = "wikipush"
    user_name="Wolfgang Fahl"

    program_license = '''%s

  Created by %s on %s.
  Copyright 2020 Wolfgang Fahl. All rights reserved.

  Licensed under the Apache License 2.0
  http://www.apache.org/licenses/LICENSE-2.0

  Distributed on an "AS IS" basis without warranties
  or conditions of any kind, either express or implied.

''' % (program_shortdesc,user_name, str(__date__))
    try:
        forceRebuild=False
        # Setup argument parser
        parser = ArgumentParser(description=program_license, formatter_class=RawDescriptionHelpFormatter)
        parser.add_argument("-d", "--debug", dest="debug",   action="store_true", help="set debug level [default: %(default)s]")
        parser.add_argument('-V', '--version', action='version', version=program_version_message)
        parser.add_argument("-f", "--forceRebuild", dest="forceRebuild",   action="store_true", help="shall the applications rebuild be forced (with stop and remove of existing containers)")
        mwCluster=MediaWikiCluster()
        mwCluster.start(forceRebuild)
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
    