'''
Created on 2021-06-14

@author: wf
'''
import datetime
import socket
import unittest
import io
import os
import re
import mwdocker
from mwdocker.version import Version
from mwdocker.mwcluster import MediaWikiCluster
from mwdocker.config import MwClusterConfig
from argparse import ArgumentParser

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
        
    def getMwConfig(self,argv=[]):
        """
        get a mediawiki configuration for the given command line arguments
        """
        parser = ArgumentParser()
        mwClusterConfig=MwClusterConfig()
        mwClusterConfig.addArgs(parser)
        args = parser.parse_args(argv)
        mwClusterConfig.fromArgs(args)
        return mwClusterConfig
    
    def getMwCluster(self,argv=[],createApps:bool=True):
        """
        get a mediawiki cluster as configured by the command line arguments
        """
        config=self.getMwConfig(argv)
        mwCluster=MediaWikiCluster(config=config)
        mwCluster.checkDocker()
        if createApps:
            self.home="/tmp"
            mwCluster.createApps(home=self.home)
        return mwCluster
          
    def testComposePluginInstalled(self):
        '''
        make sure the docker compose command is available
        '''
        self.assertTrue(docker.compose.is_installed())   
        
    def testGenerateDockerFiles(self):
        '''
        test generating the docker files
        '''
        mwCluster=self.getMwCluster()
        for _index,version in enumerate(mwCluster.config.versions):
            mwApp=mwCluster.apps[version]
            config=mwApp.config
            epath=f"{self.home}/.pymediawikidocker/{config.container_base_name}"
            self.assertTrue(os.path.isdir(epath))
            for fname in [
                    'Dockerfile',
                    'docker-compose.yml',
                    'startRunJobs.sh',
                    'LocalSettings.php',
                    'initdb.sh',
                    'update.sh',
                    'addCronTabEntry.sh',
                    'installExtensions.sh',
                    'upload.ini',
                    'addSysopUser.sh',
                    'phpinfo.php',
                    'wiki.sql',
                    'composer.local.json',
                    'plantuml.sh'
                ]:
                fpath=f"{epath}/{fname}"
                self.assertTrue(os.path.isfile(fpath))
    
    def testInstallation(self):
        '''
        test the MediaWiki docker image installation
        '''
        mwCluster=self.getMwCluster()
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
        #debug=True
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
        mwCluster=self.getMwCluster()
        exitCode=mwCluster.check()
        self.assertEqual(0,exitCode)
        
    def testInstallationWithSemanticMediaWiki(self):
        '''
        test MediaWiki with SemanticMediaWiki 
        and composer
        '''
        mwCluster=self.getMwCluster(["--prefix","smw4",
            "--versionList","1.39.3",
            "--smwVersion","4.1.1",
            "--basePort","9480",
            "--sqlBasePort","10306"],createApps=False)
        mwCluster.config.addExtensions(["MagicNoCache","Data Transfer","Page Forms","Semantic Result Formats"])
        apps=mwCluster.createApps()
        app=apps["1.39.3"]
        app.start(forceRebuild=True)
        
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
        for argv,expected in [
            (["-h"],"--user"),
            (["-V"],Version.updated),
            (["--list"],"1.39.3")
        ]:
            try:
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    mwdocker.mwcluster.main(argv)
                #self.fail("system exit expected")
            except SystemExit:
                pass
            stdout_txt=stdout.getvalue()
            debug=self.debug
            debug=True
            if debug:
                print(stdout_txt)
            self.assertTrue(expected in stdout_txt)
        
    def testGraphViz(self):
        '''
        create graphviz documentation for wiki
        '''
        mwCluster=self.getMwCluster()
        isodate=datetime.datetime.now().isoformat()
        lines=f"""// generated by {__file__} on {isodate}
digraph mwcluster {{
  rankdir="RL"
"""
        for index,version in enumerate(mwCluster.config.versions):
            mwApp=mwCluster.apps[version]
            config=mwApp.config
            lines+=f'''  mew{index} [ label="{config.container_base_name}-mw\\n{config.fullVersion}\\nport {config.port}" ]\n'''
            lines+=f'''  mdb{index} [ label="{config.container_base_name}-db\\nMariaDB {config.mariaDBVersion}\\nport {config.sqlPort}" ]\n'''
            lines+=f'''  subgraph cluster_{index}{{\n'''
            lines+=f'''    label="{config.container_base_name}"\n'''
            lines+=f'''    mew{index}->mdb{index}\n'''
            lines+=f'''  }}\n'''
        lines+="}"
        show=self.debug
        #show=True
        # show only for wiki documentation
        if show:
            print (lines)
   
if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()