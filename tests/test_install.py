'''
Created on 2021-01-25

@author: wf
'''
import unittest
import docker
from mwdocker.mwimage import MWImage
import warnings

class TestInstall(unittest.TestCase):
    '''
    test MediaWiki Docker images installation using
    https://github.com/docker/docker-py
    '''

    def setUp(self):
        self.debug=False
        # filter annoying resource warnings
        warnings.filterwarnings(action="ignore", message="unclosed", category=ResourceWarning)
        pass

    def tearDown(self):
        pass
    
    def log(self,msg):
        if self.debug:
            print(msg)
    
    def testInstallation(self):
        '''
        test the MediaWiki docker image installation
        '''
        versions=["1.27.7","1.31.14","1.35.2"]
        client = docker.from_env()
        il=client.images.list()
        print(il)
        cl=client.containers.list()
        print(cl)
        for version in versions:
            mwImage=MWImage(client,version=version)
            print(f"pulling Mediawiki {version} docker image ...")
            mwImage.pull()
        
        

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()