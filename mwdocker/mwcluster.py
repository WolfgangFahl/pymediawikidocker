'''
Created on 2021-08-06
@author: wf
'''
from mwdocker.docker import DockerApplication

class MediaWikiCluster(object):
    '''
    a cluster of mediawiki docker Applications
    '''

    def __init__(self,debug=False,sqlPort=9306,basePort=9080,versions=["1.27.7","1.31.14","1.35.2"],networkName="mwNetwork",mariaDBVersion="10.5",mySQLRootPassword="insecurepassword"):
        '''
        Constructor
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
                
    def start(self,forceRebuild:bool=False):
        '''
        create and start the composer applications
        '''           
        for i,version in enumerate(self.versions):
            mwApp=self.getDockerApplication(i,version)
            mwApp.generateAll()
            mwApp.up(forceRebuild=forceRebuild) 
            self.apps[version]=mwApp        
            
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
        mwApp=DockerApplication(version=version,debug=True,mariaDBVersion=self.mariaDBVersion,port=port,sqlPort=sqlPort)
        return mwApp
            
    def genDockerFiles(self):
        '''
        generate all docker files
        '''
        for i,version in enumerate(self.versions):
            mwApp=self.getDockerApplication(i,version)
            mwApp.generateAll()
    