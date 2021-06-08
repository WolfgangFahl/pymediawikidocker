'''
Created on 2021-01-25

@author: wf
'''
import unittest
import docker
from mwdocker.dimage import DockerImage
import warnings

class TestInstall(unittest.TestCase):
    '''
    test MediaWiki Docker images installation using
    https://github.com/docker/docker-py
    '''

    def setUp(self):
        self.debug=False
        self.client = docker.from_env()
        # filter annoying resource warnings
        warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning)
        pass

    def tearDown(self):
        pass
    
    def log(self,msg):
        if self.debug:
            print(msg)
            
            
    def testDockerCredentialDesktop(self):
        '''
        check that docker-credential-desktop is available
        '''
        mwImage=DockerImage(self.client,debug=True,doCheckDocker=False)
        mwImage.checkDocker()
    
    def testInstallation(self):
        '''
        test the MediaWiki docker image installation
        '''
        versions=["1.27.7","1.31.14","1.35.2"]
        
        il=self.client.images.list()
        print(il)
        cl=self.client.containers.list()
        print(cl)
        mariaImage=DockerImage(self.client,name="mariadb",version="10.5")
        mariaImage.pull()
        for version in versions:
            mwImage=DockerImage(self.client,version=version,debug=True)
            mwImage.pull()

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()