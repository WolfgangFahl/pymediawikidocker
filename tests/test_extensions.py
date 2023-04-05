'''
Created on 2021-06-23

@author: wf
'''
import unittest
from mwdocker.mwcluster import MediaWikiCluster
from mwdocker.mw import ExtensionList, Extension
from tests.basetest import Basetest

class TestExtensions(Basetest):
    '''
    test the extension handling
    '''

    def setUp(self):
        Basetest.setUp(self)
        pass
    
    def testExtensionDetailsFromUrl(self):
        '''
        test getting details of an extension
        '''
        ext=Extension()
        ext.name="UrlGetParameters"
        ext.url="https://www.mediawiki.org/wiki/Extension:UrlGetParameters"
        debug=self.debug
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
        extensionNames=["Admin Links","BreadCrumbs2","Variables","ImageMap"]
        extMap=MediaWikiCluster.getExtensionMap(extensionNames,extensionJsonFile)
        mwShortVersion="131"
        expectedUrl={
            "Admin Links": "https://www.mediawiki.org/wiki/Extension:Admin_Links",
            "BreadCrumbs2": "https://www.mediawiki.org/wiki/Extension:BreadCrumbs2"
        }
        expectedScript={
            "Admin Links":"git clone https://github.com/wikimedia/mediawiki-extensions-AdminLinks --single-branch --branch master AdminLinks"
        }
        for extensionName in extensionNames:
            ext=extMap[extensionName]
            if self.debug:
                print (ext)
                print (ext.asScript())
                localSettingsLine=ext.getLocalSettingsLine(mwShortVersion)
                print(localSettingsLine)
            if extensionName in expectedUrl:
                self.assertEqual(expectedUrl[extensionName],ext.url)
            if extensionName in expectedScript:
                self.assertEqual(expectedScript[extensionName],ext.asScript())
        pass
    
    def testSpecialVersionHandling(self):
        '''
        https://github.com/WolfgangFahl/pymediawikidocker/issues/16
        Option to Extract extension.json / extensionNameList contents from Special:Version 
        '''
        debug=self.debug
        #debug=False
        for url in [
            #"https://www.openresearch.org/wiki/Special:Version",
            #"https://confident.dbis.rwth-aachen.de/or/index.php?title=Special:Version",
            "https://wiki.bitplan.com/index.php/Special:Version"
            
        ]:
            extList=ExtensionList.fromSpecialVersion(url,showHtml=False,debug=debug)
            extList.extensions=sorted(extList.extensions,key=lambda ext:ext.name)
            print(f"found {len(extList.extensions)} extensions for {url}")
            if debug:
                for ext in extList.extensions:
                    print (ext)
                for ext in extList.extensions:
                    print (ext.asWikiMarkup())
                print(extList.toJSON())    
                

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()