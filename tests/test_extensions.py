"""
Created on 2021-06-23

@author: wf
"""

import io
import json
import os
import tempfile
from contextlib import redirect_stdout

from basemkit.basetest import Basetest

from mwdocker.config import MwClusterConfig
from mwdocker.mw import Extension, ExtensionList


class TestExtensions(Basetest):
    """
    test the extension handling
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)

    def testReadExtensions(self):
        """
        read the extensions
        """
        extensionList = ExtensionList.restore()
        self.assertTrue(len(extensionList.extensions) >= 35)
        pass

    def test_convert_to_yaml(self):
        """
        test extension list conversion to yaml
        """
        extension_list = ExtensionList.restore()
        yaml_str = extension_list.to_yaml()
        if self.debug:
            print(yaml_str)
        self.assertTrue("- name: Page Forms" in yaml_str)

    def testExtensionDetailsFromUrl(self):
        """
        test getting details of an extension
        """
        ext = Extension(
            name="UrlGetParameters",
            url="https://www.mediawiki.org/wiki/Extension:UrlGetParameters",
        )
        debug = self.debug
        ext.getDetailsFromUrl(showHtml=debug)
        if debug:
            print(ext)
        self.assertEqual(
            "https://github.com/wikimedia/mediawiki-extensions-UrlGetParameters",
            ext.giturl,
        )

    def testExtensionHandling(self):
        """
        test extension handling
        """
        jsonStr = """{
    "extensions": [
        {
            "giturl": "https://github.com/wikimedia/mediawiki-extensions-Variables",
            "localSettings": "wfLoadExtension( 'Variables' );",
            "name": "Variables",
            "purpose": "The Variables extension allows you to define a variable on a page, use it later in that same page or included templates",
            "since": "2011-11-13T00:00:00",
            "url": "https://www.mediawiki.org/wiki/Extension:Variables"
        }
    ]
}"""
        extensionJsonFile = "/tmp/extensions4Mw.json"
        with open(extensionJsonFile, "w") as jsonFile:
            jsonFile.write(jsonStr)
        extensionNames = ["Admin Links", "BreadCrumbs2", "Variables", "ImageMap"]
        config = MwClusterConfig()
        extMap = config.getExtensionMap(extensionNames, extensionJsonFile)
        mwShortVersion = "131"
        expectedUrl = {
            "Admin Links": "https://www.mediawiki.org/wiki/Extension:Admin_Links",
            "BreadCrumbs2": "https://www.mediawiki.org/wiki/Extension:BreadCrumbs2",
        }
        expectedScript = {
            "Admin Links": 'git_get "https://github.com/wikimedia/mediawiki-extensions-AdminLinks" "AdminLinks" "--single-branch --branch master"'
        }
        for extensionName in extensionNames:
            ext = extMap[extensionName]
            if self.debug:
                print(ext)
                print(ext.asScript())
                localSettingsLine = ext.getLocalSettingsLine(mwShortVersion)
                print(localSettingsLine)
            if extensionName in expectedUrl:
                self.assertEqual(expectedUrl[extensionName], ext.url)
            if extensionName in expectedScript:
                self.assertEqual(expectedScript[extensionName], ext.asScript())
        pass

    def testSpecialVersionHandling(self):
        """
        https://github.com/WolfgangFahl/pymediawikidocker/issues/16
        Option to Extract extension.json / extensionNameList contents from Special:Version
        """
        debug = self.debug
        # debug=False
        for url, expected in [
            # "https://www.openresearch.org/wiki/Special:Version",
            # "https://confident.dbis.rwth-aachen.de/or/index.php?title=Special:Version",
            ("https://wiki.bitplan.com/index.php/Special:Version", 36),
            ("https://cr.bitplan.com/index.php/Special:Version", 35),
        ]:
            extList = ExtensionList.fromSpecialVersion(url, showHtml=False, debug=debug)
            extList.extensions = sorted(extList.extensions, key=lambda ext: ext.name)
            print(
                f"checking {len(extList.extensions)}>={expected} extensions for {url}"
            )
            self.assertTrue(len(extList.extensions) >= expected)
            if debug:
                for ext in extList.extensions:
                    print(ext)
                for ext in extList.extensions:
                    print(ext.asWikiMarkup())
                print(extList.toJSON())

    def test_duplicate_extensions(self):
        """
        Test the handling of duplicate extensions when
        loading from both default and custom JSON files
        """
        extension_dict = {
            "extensions": [
                {
                    "name": "Flex Diagrams",
                    "extension": "FlexDiagrams",
                    "giturl": "https://gerrit.wikimedia.org/r/mediawiki/extensions/FlexDiagrams.git",
                    "url": "https://www.mediawiki.org/wiki/Extension:Flex_Diagrams",
                },
                {
                    "name": "Page Forms",
                    "extension": "PageForms",
                    "url": "https://www.mediawiki.org/wiki/Extension:Page_Forms",
                    "composer": '"mediawiki/page-forms": "^5.8"',
                },
            ]
        }
        temp_json = tempfile.NamedTemporaryFile(mode="w+", delete=False, suffix=".json")
        json.dump(extension_dict, temp_json)
        temp_json.close()

        config = MwClusterConfig()
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            ext_map = config.getExtensionMap(
                ["Page Forms", "Flex Diagrams"], temp_json.name
            )
        log_msg = stdout.getvalue()
        debug = True
        if debug:
            print(ext_map)
        os.unlink(temp_json.name)
        self.assertEqual(2, len(ext_map))
        self.assertTrue("5.8" in ext_map["Page Forms"].composer)
        self.assertTrue("overriding Page Forms" in log_msg)
