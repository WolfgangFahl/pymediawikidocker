'''
Created on 2023-04-06

@author: wf
'''
from tests.basetest import Basetest
from mwdocker.config import MwClusterConfig, Host
import json
from argparse import ArgumentParser
import dataclasses

class TestConfig(Basetest):
    '''
    test the Mediawiki Cluster configuration
    '''
    
    def testDefaults(self):
        """
        test the defaults
        """
        mwClusterConfig=MwClusterConfig()
        expected={'version': '1.39.3', 'smwVersion': None, 
                  'extensionNameList': ['Admin Links', 'Header Tabs', 'SyntaxHighlight', 'Variables'], 
                  'extensionJsonFile': None, 'user': 'Sysop', 'prefix': 'mw', 
                  'password_length': 15, 'password': 'sysop-1234!', 
                  'mySQLRootPassword': None, 'mySQLPassword': None, 
                  'logo': '$wgResourceBasePath/resources/assets/wiki.png',
                   'port': 9080, 'sqlPort': 9306, 'prot': 'http', 
                   'host': Host.get_default_host(), 'script_path': '', 'container_base_name': 'mw-139', 'networkName': 'mwNetwork', 'mariaDBVersion': '10.11', 'forceRebuild': False, 'debug': False, 'verbose': True, 'wikiId': None, 'versions': ['1.35.10','1.38.6', '1.39.3'], 'basePort': 9080}

        mwd=mwClusterConfig.as_dict()
        debug=self.debug
        #debug=True
        if debug:
            print(mwd)
            print(json.dumps(mwd,indent=2))
        self.assertEqual(expected,mwd)
            
    def testArgs(self):
        """
        test command line argument handling
        """
        parser = ArgumentParser()
        mwClusterConfig=MwClusterConfig()
        mwClusterConfig.addArgs(parser)
        argv=["--prot","https"]
        args = parser.parse_args(argv)
        mwClusterConfig.fromArgs(args)
        mwd=dataclasses.asdict(mwClusterConfig)
        debug=self.debug
        #debug=True
        if debug:
            print(json.dumps(mwd,indent=2))
        self.assertEqual("https",mwClusterConfig.prot)
        
    def test_random_password(self):
        """
        test the random password generation
        """
        config=MwClusterConfig()
        for length,chars in [(11,15),(13,18),(15,20)]:
            rp=config.random_password(length)
            debug=self.debug
            if debug:
                print(f"{length} bytes:{len(rp)} chars:{rp}")
            self.assertEqual(chars,len(rp))    