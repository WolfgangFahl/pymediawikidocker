'''
Created on 2021-06-23

@author: wf
'''
from lodstorage.jsonable import JSONAble, JSONAbleList
from lodstorage.lod import LOD
from datetime import datetime
from mwdocker.webscrape import WebScrape
import os
import urllib

class ExtensionList(JSONAbleList):
    '''
    represents a list of MediaWiki extensions
    '''
    def __init__(self):
        '''
        constructor
        '''
        super(ExtensionList, self).__init__('extensions', Extension)
    
    @staticmethod
    def storeFilePrefix():
        '''
        get my storeFilePrefix
        
        Returns:
            str: the path to where my stored files (e.g. JSON) should be kept
        '''
        scriptdir=os.path.dirname(os.path.realpath(__file__))
        resourcePath=os.path.realpath(f"{scriptdir}/resources")
        storeFilePrefix=f"{resourcePath}/extensions"
        return storeFilePrefix
    
    @classmethod
    def fromSpecialVersion(cls,url:str,excludes=["skin","editor"],showHtml=False,debug=False):
        '''
        get an extension List from the given url
        
        Args:
            url(str): the Special:Version MediaWiki page to read the information from
            exclude (list): a list of types of extensions to exclude
            showHtml(bool): True if the html code should be printed for debugging
            debug(bool): True if debugging should be active
            
        Returns:
            ExtensionList: an extension list derived from the url
        '''
        webscrape=WebScrape()
        soup=webscrape.getSoup(url, showHtml=showHtml)
        
        # search for
        # <tr class="mw-version-ext" id="mw-version-ext-media-PDF_Handler">
        exttrs=soup.findAll(attrs={"class" : "mw-version-ext"})
        extList=ExtensionList()
        for exttr in exttrs:
            if showHtml:
                print (exttr)
            doExclude=False
            for exclude in excludes:
                if f"-{exclude}-" in exttr.get("id"):
                    doExclude=True
            if not doExclude:
                ext=Extension.fromSpecialVersionTR(exttr,debug=debug)
                if ext:
                    extList.extensions.append(ext)
        return extList
        
        
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
            "extension": "AdminLinks",
            "url": "https://www.mediawiki.org/wiki/Extension:Admin_Links",
            "purpose": """Admin Links is an extension to MediaWiki that defines a special page, "Special:AdminLinks",
that holds links meant to be helpful for wiki administrators;
it is meant to serve as a "control panel" for the functions an administrator would typically perform in a wiki.
All users can view this page; however, for those with the 'adminlinks' permission (sysops/administrators, by default),
a link to the page also shows up in their "Personal URLs", between "Talk" and "Preferences".""",
            "since": datetime.fromisoformat("2009-05-13"),
            "giturl":"https://gerrit.wikimedia.org/r/mediawiki/extensions/AdminLinks.git",
            "localSettings": ""
        }]
        return samplesLOD
    
    @classmethod
    def fromSpecialVersionTR(cls,exttr,debug=False):
        '''
        Construct an extension from a beautifl soup TR tag
        derived from Special:Version
        
        Args:
            exttr: the beautiful soup TR tag
            debug(bool): if True show debugging information
        '''
        ext=None
        extNameTag=exttr.find(attrs={"class" : "mw-version-ext-name"})
        extPurposeTag=exttr.find(attrs={"class" : "mw-version-ext-description"})
        if extNameTag:
            ext=Extension()
            ext.name=extNameTag.string
            ext.extension=ext.name.replace(" ","")
            ext.url=extNameTag.get("href")
            if extPurposeTag and extPurposeTag.string:
                ext.purpose=extPurposeTag.string
            ext.getDetailsFromUrl(debug=debug)
        return ext

    def __init__(self):
        '''
        Constructor
        '''
        
    def __str__(self):
        text=""
        delim=""
        samples=self.getJsonTypeSamples()
        for attr in LOD.getFields(samples):
            if hasattr(self, attr):
                text+=f"{delim}{attr}={self.__dict__[attr]}"
                delim="\n"
        return text
    
    def getDetailsFromUrl(self,showHtml=False,debug=False):
        '''
        get more details from my url
        '''
        webscrape=WebScrape()
        try:
            soup=webscrape.getSoup(self.url, showHtml=showHtml)
            for link in soup.findAll('a',attrs={"class" : "external text"}):
                if ("GitHub" == link.string) or ("git repository URL") == link.string:
                    self.giturl=link.get('href')
        except urllib.error.HTTPError as herr:
            if debug:
                print(f"HTTPError {str(herr)} for {self.url}")
        
    
    def asWikiMarkup(self):
        '''
        return me as wiki Markup
        '''
        samples=self.getJsonTypeSamples()
        nameValues=""
        for attr in LOD.getFields(samples):        
            if hasattr(self, attr):
                nameValues+=f"|{attr}={self.__dict__[attr]}\n"
        wikison=f"""{{{{Extension
{nameValues}
}}}}"""
        return wikison
    
    
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
            text = "# no installation script command specified"
            if hasattr(self,"composer"):
                text+=f"\n# installed with composer require {self.composer}"
            return text
        