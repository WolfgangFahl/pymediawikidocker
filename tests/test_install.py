'''
Created on 2021-01-25

@author: wf
'''
import unittest
from mwdocker.mwcluster import MediaWikiCluster
from mwdocker.docker import DockerMap
from python_on_whales import docker

class TestInstall(unittest.TestCase):
    '''
    test MediaWiki Docker images installation using
    https://pypi.org/project/python-on-whales/
    '''

    def setUp(self):
        self.debug=True
        
    def tearDown(self):
        pass
        
    def testGenerateDockerFiles(self):
        '''
        test generating the docker files
        '''
        mwCluster=MediaWikiCluster()
        mwCluster.genDockerFiles()
    
    def testInstallation(self):
        '''
        test the MediaWiki docker image installation
        '''
        mwCluster=MediaWikiCluster()
        mwCluster.start(forceRebuild=True)
        imageMap=DockerMap.getImageMap()
        print(imageMap)
        
   
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()