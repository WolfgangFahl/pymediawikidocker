'''
Created on 2021-06-23

@author: wf
'''
from lodstorage.jsonable import JSONAble, JSONAbleList
from datetime import datetime
import os

class ExtensionList(JSONAbleList):
    '''
    represents a list of MediaWiki extensions
    '''
    def __init__(self):
        super(ExtensionList, self).__init__('extensions', Extension)
    
    @staticmethod
    def storeFilePrefix():
        scriptdir=os.path.dirname(os.path.realpath(__file__))
        resourcePath=os.path.realpath(f"{scriptdir}/resources")
        storeFilePrefix=f"{resourcePath}/extensions"
        return storeFilePrefix
        
    @classmethod 
    def restore(cls):
        '''
        restore 
        '''
        extList=ExtensionList()
        extList.restoreFromJsonFile(ExtensionList.storeFilePrefix())
        return extList
        
    def save(self):
        '''
        save the extension list
        '''
        super().storeToJsonFile(ExtensionList.storeFilePrefix())
    
class Extension(JSONAble):
    '''
    represents a MediaWiki extension
    '''
    @classmethod
    def getSamples(cls):
        samplesLOD = [{
            "name": "Admin Links",
            "url": "https://www.mediawiki.org/wiki/Extension:Admin_Links",
            "purpose": """Admin Links is an extension to MediaWiki that defines a special page, "Special:AdminLinks",
that holds links meant to be helpful for wiki administrators;
it is meant to serve as a "control panel" for the functions an administrator would typically perform in a wiki.
All users can view this page; however, for those with the 'adminlinks' permission (sysops/administrators, by default),
a link to the page also shows up in their "Personal URLs", between "Talk" and "Preferences".""",
            "since": datetime.fromisoformat("2009-05-13"),
            "giturl":"https://gerrit.wikimedia.org/r/mediawiki/extensions/AdminLinks.git",
            "localSettings": "wfLoadExtension( 'AdminLinks' );"
        }]
        return samplesLOD

    def __init__(self):
        '''
        Constructor
        '''
        
    def asScript(self):
        '''
        return me as a shell Script command line list
        '''
        if hasattr(self, "giturl"):
            return (f"git clone {self.giturl}")
        else:
            return ""
        