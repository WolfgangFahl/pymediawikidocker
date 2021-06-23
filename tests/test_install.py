'''
Created on 2021-06-14

@author: wf
'''
import unittest
import io
import mwdocker
from mwdocker.mwcluster import MediaWikiCluster
from python_on_whales import docker
from contextlib import redirect_stdout

class TestInstall(unittest.TestCase):
    '''
    test MediaWiki Docker images installation using
    https://pypi.org/project/python-on-whales/
    '''

    def setUp(self):
        self.debug=True
        self.versions=MediaWikiCluster.defaultVersions
        
    def tearDown(self):
        pass
    
    def testComposePluginInstalled(self):
        '''
        make sure the docker compose command is available
        '''
        self.assertTrue(docker.compose.is_installed())
        
        
    def testGenerateDockerFiles(self):
        '''
        test generating the docker files
        '''
        mwCluster=MediaWikiCluster(self.versions)
        mwCluster.createApps()
    
    def testInstallation(self):
        '''
        test the MediaWiki docker image installation
        '''
        mwCluster=MediaWikiCluster(self.versions,debug=self.debug)
        mwCluster.createApps()
        mwCluster.start(forceRebuild=True)
        apps=mwCluster.apps.values()
        self.assertEqual(len(mwCluster.versions),len(apps))
        for mwApp in apps:
            self.assertTrue(mwApp.dbContainer is not None)
            self.assertTrue(mwApp.mwContainer is not None)
            self.assertTrue(mwApp.checkDBConnection())
            userCountRecords=mwApp.sqlQuery("select count(*) from user;")
            print(userCountRecords)
        mwCluster.close()
        
    def testInstallationWithSemanticMediaWiki(self):
        '''
        test MediaWiki with SemanticMediaWiki as per 
        '''
        mwCluster=MediaWikiCluster(versions=["1.31.14"],smwVersion="3.2.3",basePort=9480,sqlPort=10306)
        mwCluster.createApps()
        mwCluster.start(forceRebuild=True)
        
    def testInstallationWithMissingLocalSettingsTemplate(self):
        '''
        test a cluster with no LocalSettingsTemplate available
        '''
        return
        mwCluster=MediaWikiCluster(versions=['1.36.0'])
        mwCluster.createApps()
        mwCluster.start()
        
    def testWikiUser(self):
        '''
        test the wikiUser handling
        '''
        mwCluster=MediaWikiCluster(MediaWikiCluster.defaultVersions,wikiIdList=["mw27test","mw31test","mw35test","mw36test"])
        mwCluster.createApps()
        for mwApp in mwCluster.apps.values():
            wikiUser=mwApp.createWikiUser(store=False)
            if self.debug:
                print(wikiUser)
        
    def testMwClusterCommandLine(self):
        '''
        test the mwCluster Command Line
        '''
        argv=["-h"]
        try:
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                mwdocker.mwcluster.main(argv)
            self.fail("system exit expected")
        except SystemExit:
            pass
        self.assertTrue("--wikiIdList" in stdout.getvalue())
        # just for debugging command line handling
        # mwdocker.mwcluster.main([])
   
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()