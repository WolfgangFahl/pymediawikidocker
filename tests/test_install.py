'''
Created on 2021-01-25

@author: wf
'''
import unittest
import docker
from mwdocker.mwcluster import MediaWikiCluster
from mwdocker.dimage import DockerClient,DockerImage
import warnings

class TestInstall(unittest.TestCase):
    '''
    test MediaWiki Docker images installation using
    https://github.com/docker/docker-py
    '''

    def setUp(self):
        self.debug=True
        
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
        dockerClient=DockerClient.getInstance()
        mwImage=DockerImage(dockerClient,debug=self.debug,doCheckDocker=False)
        mwImage.checkDocker()
    
    def testInstallation(self):
        '''
        test the MediaWiki docker image installation
        '''
        mwCluster=MediaWikiCluster()
        mwCluster.prepareImages()
            
        imageMap=mwCluster.dockerClient.getImageMap()
        if self.debug:
            print(imageMap)
        # make sure there are 4 containers
        self.assertEqual(4,len(mwCluster.containers))
        # make sure the images of all containers are in the imageMap
        for container in mwCluster.containers:
            tag=container.image.tags[0]
            self.assertTrue(tag in imageMap)
       
        cl=mwCluster.client.containers.list()
        if self.debug:
            print(cl)
        # make sure there are at least 4 running containers
        self.assertTrue(len(cl)>=4)
        
   
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()