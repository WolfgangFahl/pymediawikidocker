'''
Created on 2021-06-23

@author: wf
'''
import unittest
from mwdocker.mw import ExtensionList

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
        extList=ExtensionList.restore()
        extMap,duplicates=extList.getLookup("name")
        self.assertEqual(0,len(duplicates))
        adminLinks=extMap["Admin Links"]
        self.assertEqual("https://www.mediawiki.org/wiki/Extension:Admin_Links",adminLinks.url)
        if self.debug:
            print (adminLinks.asScript())
        self.assertEqual(adminLinks.asScript(),"git clone https://gerrit.wikimedia.org/r/mediawiki/extensions/AdminLinks.git")
        pass


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()