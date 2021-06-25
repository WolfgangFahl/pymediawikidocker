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
        
    def getLocalSettingsLine(self,mwShortVersion:str):
        '''
        get my local settings line
        
        Args:
            mwShortVersion(str): the MediaWiki short version e.g. 127
        
        Returns:
            entry for LocalSettings
        '''
        localSettingsLine=f"wfLoadExtension( '{self.extension}' );"
        if hasattr(self,"require_once_until"):
            if self.require_once_until>=mwShortVersion:
                localSettingsLine=f'require_once "$IP/extensions/{self.extension}/{self.extension}.php";'

        if hasattr(self,"localSettings"):
            localSettingsLine+=f"\n  {self.localSettings}"
        return localSettingsLine
    
    def asScript(self,branch="master"):
        '''
        return me as a shell Script command line list
        
        Args:
            branch(str): the branch to clone 
        '''
        if hasattr(self, "giturl"):
            if "//github.com/wikimedia/" in self.giturl:
                # glone from the branch
                return (f"git clone {self.giturl} --single-branch --branch {branch} {self.extension}")
            else:    
                return (f"git clone {self.giturl} {self.extension}")
        else:
            return "# no installation script command specified"
        