'''
Created on 2021-06-23

@author: wf
'''
import unittest
from mwdocker.mwcluster import MediaWikiCluster
from mwdocker.mw import ExtensionList, Extension

class TestExtensions(unittest.TestCase):
    '''
    test the extension handling
    '''

    def setUp(self):
        self.debug=True
        pass


    def tearDown(self):
        pass
    
    def testExtensionDetailsFromUrl(self):
        '''
        test getting details of an extension
        '''
        ext=Extension()
        ext.name="UrlGetParameters"
        ext.url="https://www.mediawiki.org/wiki/Extension:UrlGetParameters"
        debug=False
        ext.getDetailsFromUrl(showHtml=debug)
        if debug:
            print(ext)
        self.assertEqual("https://github.com/wikimedia/mediawiki-extensions-UrlGetParameters",ext.giturl)
        


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
    
    def testSpecialVersionHandling(self):
        '''
        https://github.com/WolfgangFahl/pymediawikidocker/issues/16
        Option to Extract extension.json / extensionNameList contents from Special:Version 
        '''
        debug=self.debug
        #debug=False
        for url in [
            "https://wiki.bitplan.com/index.php/Special:Version",
            "https://www.openresearch.org/wiki/Special:Version"
        ]:
            extList=ExtensionList.fromSpecialVersion(url,showHtml=False,debug=True)
            extList.extensions=sorted(extList.extensions,key=lambda ext:ext.name)
            print(f"found {len(extList.extensions)} extensions for {url}")
            for ext in extList.extensions:
                print (ext)
            for ext in extList.extensions:
                print (ext.asWikiMarkup())
            print(extList.toJSON())    
                


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()