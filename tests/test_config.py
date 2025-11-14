"""
Created on 2023-04-06

@author: wf
"""

import json

from basemkit.basetest import Basetest

from mwdocker.config import Host, MwClusterConfig, MwConfig
from mwdocker.mwdocker_cmd import MediaWikiDockerCmd
from mwdocker.version import Version


class TestConfig(Basetest):
    """
    test the Mediawiki Cluster configuration
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def testDefaults(self):
        """
        test the defaults
        """
        mwClusterConfig = MwClusterConfig()
        expected = {
            "version": "1.39.15",
            "smw_version": None,
            "extensionNameList": [
                "Admin Links",
                "Header Tabs",
                "ParserFunctions",
                "SyntaxHighlight",
                "Variables",
            ],
            "extensionJsonFile": None,
            "user": "Sysop",
            "prefix": "mw",
            "password_length": 15,
            "password": "sysop-1234!",
            "random_password": False,
            "force_user": False,
            "mySQLRootPassword": None,
            "mySQLPassword": None,
            "logo": "$wgResourceBasePath/resources/assets/wiki.png",
            "port": 9080,
            "sql_port": 9306,
            "prot": "http",
            "host": Host.get_default_host(),
            "lenient": True,
            "article_path": "",
            "script_path": "",
            "container_base_name": "mw-139",
            "db_container_name": "mw-139-db",
            "networkName": "mwNetwork",
            "mariaDBVersion": "11.4",
            "forceRebuild": False,
            "debug": False,
            "verbose": True,
            "wikiId": None,
            "versions": ["1.35.13", "1.39.15", "1.43.5", "1.44.2"],
            "base_port": 9080,
            "gid": 33,
            "uid": 33,
            "bind_mount": False,
            "docker_path": mwClusterConfig.docker_path,
        }

        mwd = mwClusterConfig.as_dict()
        debug = self.debug
        # debug=True
        if debug:
            print(mwd)
            print(json.dumps(mwd, indent=2))
        self.maxDiff = None
        self.assertEqual(expected, mwd)

    def testSaveAndLoad(self):
        """
        test saving a reloading configuration
        """
        config = MwConfig()
        config_dict = config.as_dict()
        debug = self.debug
        if debug:
            print(config.as_json())
        config.docker_path = "/tmp"
        path = config.save()
        if debug:
            print(path)
        config2 = config.load(path)
        if debug:
            print(config2.as_json())
        config2_dict = config.as_dict()
        for key, value in config_dict.items():
            if key != "docker_path":
                self.assertEqual(value, config2_dict[key], key)

    def testArgs(self):
        """
        test command line argument handling
        """
        mwdocker_cmd = MediaWikiDockerCmd(version=Version)
        argv_examples = [
            (
                ["--prot", "https"],
                {"prot": "https"},
            ),
            (
                ["--url", "http://profiwiki.bitplan.com"],
                {"prot": "http", "host": "profiwiki.bitplan.com", "script_path": ""},
            ),
        ]
        for argv, expected in argv_examples:
            mwClusterConfig = mwdocker_cmd.getMwConfig(argv)
            json_str = mwClusterConfig.as_json()
            debug = self.debug
            # debug = True
            if debug:
                print(json_str)
                for key, value in expected.items():
                    self.assertEqual(value, getattr(mwClusterConfig, key))

    def test_random_password(self):
        """
        test the random password generation
        """
        config = MwClusterConfig()
        for length, chars in [(11, 15), (13, 18), (15, 20)]:
            rp = config.create_random_password(length)
            debug = self.debug
            if debug:
                print(f"{length} bytes:{len(rp)} chars:{rp}")
            self.assertEqual(chars, len(rp))
