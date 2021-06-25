'''
Created on 2021-06-23

@author: wf
'''
import unittest
from mwdocker.mwcluster import MediaWikiCluster

class TestExtensions(unittest.TestCase):
    '''
    test the extension handling
    '''

    def setUp(self):
        self.debug=True
        pass


    def tearDown(self):
        pass


    def testExtensionHandling(self):
        '''
        test extension handling
        '''
        jsonStr="""{
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
        extensionJsonFile="/tmp/extensions4Mw.json"
        with open(extensionJsonFile, "w") as jsonFile:
                jsonFile.write(jsonStr)
        extMap=MediaWikiCluster.getExtensionMap(["Admin Links","Variables"],extensionJsonFile)
        adminLinks=extMap["Admin Links"]
        self.assertEqual("https://www.mediawiki.org/wiki/Extension:Admin_Links",adminLinks.url)
        if self.debug:
            print (adminLinks.asScript())
        self.assertEqual(adminLinks.asScript(),"git clone https://github.com/wikimedia/mediawiki-extensions-AdminLinks --single-branch --branch master AdminLinks")
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()