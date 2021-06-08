'''
Created on 2021-01-25

@author: wf
'''
import unittest
import docker
from mwdocker.dimage import DockerClient,DockerImage
import warnings

class TestInstall(unittest.TestCase):
    '''
    test MediaWiki Docker images installation using
    https://github.com/docker/docker-py
    '''

    def setUp(self):
        self.debug=True
        self.dockerClient=DockerClient.getInstance()
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
        mwImage=DockerImage(self.dockerClient,debug=True,doCheckDocker=False)
        mwImage.checkDocker()
    
    def testInstallation(self):
        '''
        test the MediaWiki docker image installation
        '''
        # check that docker runs
        self.dockerClient.client.ping()
        # hard coded mediawiki versions to work with
        versions=["1.27.7","1.31.14","1.35.2"]
        
        mariaImage=DockerImage(self.dockerClient,name="mariadb",version="10.5")
        mariaImage.pull()
        containers=[]
        containers.append(mariaImage.run())
        for version in versions:
            mwImage=DockerImage(self.dockerClient,version=version,debug=True)
            mwImage.pull()
            containers.append(mwImage.run())
            
        imageMap=self.dockerClient.getImageMap()
        if self.debug:
            print(imageMap)
        # make sure there are 4 containers
        self.assertEqual(4,len(containers))
        # make sure the images of all containers are in the imageMap
        for container in containers:
            tag=container.image.tags[0]
            self.assertTrue(tag in imageMap)
        cl=self.dockerClient.client.containers.list()
        if self.debug:
            print(cl)
        # make sure there are at least 4 running containers
        self.assertTrue(3>=len(cl))

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()