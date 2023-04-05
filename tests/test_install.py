'''
Created on 2021-06-14

@author: wf
'''
import datetime
import socket
import unittest
import io
import re
import mwdocker
from mwdocker.mwcluster import MediaWikiCluster

from python_on_whales import docker
from contextlib import redirect_stdout
from tests.basetest import Basetest
from mwdocker.mariadb import MariaDB        

class TestInstall(Basetest):
    '''
    test MediaWiki Docker images installation using
    https://pypi.org/project/python-on-whales/
    '''

    def setUp(self):
        Basetest.setUp(self, debug=False)
        self.versions=MediaWikiCluster.defaultVersions
          
    def testComposePluginInstalled(self):
        '''
        make sure the docker compose command is available
        '''
        self.assertTrue(docker.compose.is_installed())   
        
    def testGenerateDockerFiles(self):
        '''
        test generating the docker files
        '''
        mwCluster=MediaWikiCluster(self.versions,extensionNameList=MediaWikiCluster.defaultExtensionNameList,smwVersion="3.2.3")
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
            dbStatus=mwApp.checkDBConnection()
            self.assertTrue(dbStatus.ok)
            userCountRecords=mwApp.sqlQuery("select count(*) from user;")
            print(userCountRecords)
        mwCluster.close()
        
    def testSocketGetHostname(self):
        """
        test for https://github.com/python/cpython/issues/79345
        """
        debug=self.debug
        debug=True
        for i,hostname in enumerate([socket.gethostname(),socket.getfqdn()]):
            if debug:
                print(f"{i}:{hostname}")
        for i,addr in enumerate(["localhost","127.0.0.1","fix.local","::1"]):
            try:
                hostname=socket.gethostbyaddr(addr)
                if debug:
                    print(f"{i}:{hostname}")
            except Exception as ex:
                print(f"Exception: {str(ex)}")
        
        
        
    def testMariaDBVersion(self):
        """
        test version number extraction from Maria DB
        """
        version_str="10.8.5-MariaDB-1:10.8.5+maria~ubu2204"
        version=MariaDB.getVersion(version_str)
        self.assertEqual("10.8",version)
        
    def testCheckWiki(self):
        """
        test the check wiki functionality
        """
        mwCluster=MediaWikiCluster(MediaWikiCluster.defaultVersions)
        mwCluster.createApps()
        exitCode=mwCluster.check()
        self.assertEqual(0,exitCode)
        
    def testInstallationWithSemanticMediaWiki(self):
        '''
        test MediaWiki with SemanticMediaWiki 
        and composer
        '''
        mwCluster=MediaWikiCluster(versions=["1.31.14"],smwVersion="3.2.3",basePort=9480,sqlPort=10306)
        mwCluster.extensionNameList.extend(["MagicNoCache","Data Transfer","Page Forms","Semantic Result Formats"])
        mwCluster.createApps()
        mwCluster.start(forceRebuild=True)
        
    def testInstallationWithRequireOnce(self):
        '''
        https://github.com/WolfgangFahl/pymediawikidocker/issues/15
        support legacy require_once extension registration
        '''
        mwCluster=MediaWikiCluster(versions=["1.27.7"],basePort=9481,sqlPort=10307)
        mwCluster.extensionNameList.extend(["MagicNoCache"])
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
        wikiIdList=[]
        for version in MediaWikiCluster.defaultVersions:
            minorVersion=re.sub(r"1.([0-9]+)(.[0-9]*)?",r"\1",version)
            wikiIdList.append(f"mw{minorVersion}test")
        mwCluster=MediaWikiCluster(MediaWikiCluster.defaultVersions,wikiIdList=wikiIdList)
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
        # mwdocker.mwcluster.main(["-f"])
        
    def testGraphViz(self):
        '''
        create graphviz documentation for wiki
        '''
        baseport=9080
        basesqlport=9306
        isodate=datetime.datetime.now().isoformat()
        lines=f"""// generated by {__file__} on {isodate}
digraph mwcluster {{\n"""
        for index,version in enumerate(MediaWikiCluster.defaultVersions):
            port=baseport+index
            sqlport=basesqlport+index
            v=version.replace(".","_")
            lines+=f'''  mew{index} [ label="Mediawiki {version}\\nport {port}" ]\n'''
            lines+=f'''  mdb{index} [ label="MariaDB 10.9\\nport {sqlport}" ]\n'''
            lines+=f'''  subgraph cluster_{index}{{\n'''
            lines+=f'''    label="mw{v}"\n'''
            lines+=f'''    mew{index}->mdb{index}\n'''
            lines+=f'''  }}\n'''
        lines+="}"
        show=self.debug
        show=True
        # show only for wiki documentation
        if show:
            print (lines)
   
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()