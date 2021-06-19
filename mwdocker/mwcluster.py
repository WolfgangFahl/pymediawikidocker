'''
Created on 2021-08-06
@author: wf
'''
from mwdocker.docker import DockerApplication
import secrets

class MediaWikiCluster(object):
    '''
    a cluster of mediawiki 
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
        self.containers={}
                
    def start(self,forceRebuild=False):
        '''
        prepare the images
        '''           
        for i,version in enumerate(self.versions):
            mwApp=self.getDockerApplication(i,version)
            mwApp.genDockerFile()
            mwApp.genComposerFile()
            mwApp.up()         
            
    def getDockerApplication(self,i,version):
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
            mwApp.genDockerFile()
            mwApp.genComposerFile()
    