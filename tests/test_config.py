'''
Created on 2023-04-06

@author: wf
'''
from tests.basetest import Basetest
from mwdocker.config import MwConfig,MwClusterConfig, Host
import json
from argparse import ArgumentParser

class TestConfig(Basetest):
    '''
    test the Mediawiki Cluster configuration
    '''
    
    def testDefaults(self):
        """
        test the defaults
        """
        mwClusterConfig=MwClusterConfig()
        expected={'version': '1.39.3', 'smw_version': None, 
                  'extensionNameList': ['Admin Links', 'Header Tabs', 'SyntaxHighlight', 'Variables'], 
                  'extensionJsonFile': None, 'user': 'Sysop', 'prefix': 'mw', 
                  'password_length': 15, 'password': 'sysop-1234!',
                  'random_password': False,
                  'force_user': False,
                  'mySQLRootPassword': None, 'mySQLPassword': None, 
                  'logo': '$wgResourceBasePath/resources/assets/wiki.png',
                   'port': 9080, 'sql_port': 9306, 'prot': 'http', 
                   'host': Host.get_default_host(), 'script_path': '', 'container_base_name': 'mw-139', 'networkName': 'mwNetwork', 'mariaDBVersion': '10.11', 'forceRebuild': False, 'debug': False, 'verbose': True, 
                   'wikiId': None, 'versions': ['1.35.10','1.38.6', '1.39.3'], 'base_port': 9080,
                   'docker_path': mwClusterConfig.docker_path}

        mwd=mwClusterConfig.as_dict()
        debug=self.debug
        #debug=True
        if debug:
            print(mwd)
            print(json.dumps(mwd,indent=2))
        self.assertEqual(expected,mwd)
        
    def testSaveAndLoad(self):
        """
        test saving a reloading configuration
        """
        config=MwConfig()
        config_dict=config.as_dict()
        debug=self.debug
        if debug:
            print(config.as_json())
        config.docker_path="/tmp"
        path=config.save()
        if debug:
            print(path)
        config2=config.load(path)
        if debug:
            print(config2.as_json())
        config2_dict=config.as_dict()
        for key,value in config_dict.items():
            if key!="docker_path":
                self.assertEqual(value,config2_dict[key],key)
            
    def testArgs(self):
        """
        test command line argument handling
        """
        parser = ArgumentParser()
        mwClusterConfig=MwClusterConfig()
        mwClusterConfig.addArgs(parser)
        argv_examples=[
            (
                ["--prot","https"],
                {"prot":"https"},
                
            ),
            (   
                ["--url","http://profiwiki.bitplan.com"],
                {
                    "prot":"http",
                    "host":"profiwiki.bitplan.com",
                    "script_path":""
                },
            )
        ]    
        for argv,expected in argv_examples:
            args = parser.parse_args(argv)
            mwClusterConfig.fromArgs(args)
            json_str=mwClusterConfig.as_json()
            debug=self.debug
            debug=True
            if debug:
                print(json_str)
                for key,value in expected.items():
                    self.assertEqual(value,getattr(mwClusterConfig,key))
        
    def test_random_password(self):
        """
        test the random password generation
        """
        config=MwClusterConfig()
        for length,chars in [(11,15),(13,18),(15,20)]:
            rp=config.create_random_password(length)
            debug=self.debug
            if debug:
                print(f"{length} bytes:{len(rp)} chars:{rp}")
            self.assertEqual(chars,len(rp))    