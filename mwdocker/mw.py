"""
Created on 2021-06-23

@author: wf
"""

from dataclasses import field
from datetime import datetime
import os
from typing import List, Optional, Dict
import urllib

from basemkit.yamlable import lod_storable
from lodstorage.lod import LOD
from mwdocker.webscrape import WebScrape


@lod_storable
class Extension:
    """
    represents a MediaWiki extension
    """

    name: str
    url: str
    extension: Optional[str] = None
    purpose: Optional[str] = None
    giturl: Optional[str] = None
    composer: Optional[str] = None
    wikidata_id: Optional[str] = None
    since: Optional[str] = None
    localSettings: Optional[str] = None
    require_once_until: Optional[str] = None
    tagmap: Optional[Dict[str, str]] = None  # optionally map MediaWiki REL branches e.g. { "REL1_39": "0.14.0" }

    @classmethod
    def getSamples(cls):
        samplesLOD = [
            {
                "name": "Admin Links",
                "extension": "AdminLinks",
                "url": "https://www.mediawiki.org/wiki/Extension:Admin_Links",
                "purpose": """Admin Links is an extension to MediaWiki that defines a special page, "Special:AdminLinks",
that holds links meant to be helpful for wiki administrators;
it is meant to serve as a "control panel" for the functions an administrator would typically perform in a wiki.
All users can view this page; however, for those with the 'adminlinks' permission (sysops/administrators, by default),
a link to the page also shows up in their "Personal URLs", between "Talk" and "Preferences".""",
                "since": datetime.fromisoformat("2009-05-13"),
                "giturl": "https://gerrit.wikimedia.org/r/mediawiki/extensions/AdminLinks.git",
                "localSettings": "",
            }
        ]
        return samplesLOD

    @classmethod
    def fromSpecialVersionTR(cls, exttr, debug=False):
        """
        Construct an extension from a beautifl soup TR tag
        derived from Special:Version

        Args:
            exttr: the beautiful soup TR tag
            debug(bool): if True show debugging information
        """
        ext = None
        purpose = None
        extNameTag = exttr.find(attrs={"class": "mw-version-ext-name"})
        extPurposeTag = exttr.find(attrs={"class": "mw-version-ext-description"})
        if extNameTag:
            name = extNameTag.string
            extension = name.replace(" ", "")
            url = extNameTag.get("href")
            if extPurposeTag and extPurposeTag.string:
                purpose = extPurposeTag.string
            ext = Extension(name=name, extension=extension, url=url, purpose=purpose)
            ext.getDetailsFromUrl(debug=debug)
        return ext

    def __str__(self):
        text = ""
        delim = ""
        samples = self.getSamples()
        for attr in LOD.getFields(samples):
            if hasattr(self, attr) and getattr(self, attr):
                text += f"{delim}{attr}={getattr(self,attr)}"
                delim = "\n"
        return text

    def getDetailsFromUrl(self, showHtml=False, debug=False):
        """
        get more details from my url
        """
        webscrape = WebScrape()
        try:
            soup = webscrape.getSoup(self.url, showHtml=showHtml)
            for link in soup.findAll("a", attrs={"class": "external text"}):
                if ("GitHub" == link.string) or ("git repository URL") == link.string:
                    self.giturl = link.get("href")
        except urllib.error.HTTPError as herr:
            if debug:
                print(f"HTTPError {str(herr)} for {self.url}")

    def asWikiMarkup(self):
        """
        return me as wiki Markup
        """
        samples = self.getJsonTypeSamples()
        nameValues = ""
        for attr in LOD.getFields(samples):
            if hasattr(self, attr) and getattr(self, attr):
                nameValues += f"|{attr}={getattr(self,attr)}\n"
        wikison = f"""{{{{Extension
{nameValues}
}}}}"""
        return wikison

    def getLocalSettingsLine(self, mwShortVersion: str):
        """
        get my local settings line

        Args:
            mwShortVersion(str): the MediaWiki short version e.g. 127

        Returns:
            entry for LocalSettings
        """
        localSettingsLine = ""
        if self.extension:
            localSettingsLine = f"wfLoadExtension( '{self.extension}' );"
        if self.require_once_until:
            if self.require_once_until >= mwShortVersion:
                localSettingsLine = f'require_once "$IP/extensions/{self.extension}/{self.extension}.php";'

        if self.localSettings:
            localSettingsLine += f"\n  {self.localSettings}"
        return localSettingsLine

    def asScript(self, branch: str = "master") -> str:
        """
        return me as a shell script command line string

        Args:
            branch (str): the MediaWiki branch (e.g. REL1_39)
        """
        script = ""
        if self.giturl:
            options = ""
            # check if tagmap defines a tag for this branch
            tag = None
            if self.tagmap:
                tag = self.tagmap.get(branch)
            if tag:
                # use the mapped tag
                options = f'--branch {tag}'
            elif "//github.com/wikimedia/" in self.giturl or "//gerrit.wikimedia.org" in self.giturl:
                # default WMF convention: branch per MediaWiki REL
                options = f'--single-branch --branch {branch}'
            script = f'git_get "{self.giturl}" "{self.extension}" "{options}"'
        else:
            script = "# no installation script command specified"
            if self.composer:
                script += f"\n# installed with composer require {self.composer}"
        return script



@lod_storable
class ExtensionList:
    """
    represents a list of MediaWiki extensions
    """

    extensions: List[Extension] = field(default_factory=list)

    @staticmethod
    def storeFilePrefix():
        """
        get my storeFilePrefix

        Returns:
            str: the path to where my stored files (e.g. JSON) should be kept
        """
        scriptdir = os.path.dirname(os.path.realpath(__file__))
        resourcePath = os.path.realpath(f"{scriptdir}/resources")
        storeFilePrefix = f"{resourcePath}/extensions"
        return storeFilePrefix

    @classmethod
    def fromSpecialVersion(
        cls, url: str, excludes=["skin", "editor"], showHtml=False, debug=False
    ):
        """
        get an extension List from the given url

        Args:
            url(str): the Special:Version MediaWiki page to read the information from
            exclude (list): a list of types of extensions to exclude
            showHtml(bool): True if the html code should be printed for debugging
            debug(bool): True if debugging should be active

        Returns:
            ExtensionList: an extension list derived from the url
        """
        webscrape = WebScrape()
        soup = webscrape.getSoup(url, showHtml=showHtml)

        # search for
        # <tr class="mw-version-ext" id="mw-version-ext-media-PDF_Handler">
        exttrs = soup.findAll(attrs={"class": "mw-version-ext"})
        extList = ExtensionList()
        for exttr in exttrs:
            if showHtml:
                print(exttr)
            doExclude = False
            for exclude in excludes:
                if f"-{exclude}-" in exttr.get("id"):
                    doExclude = True
            if not doExclude:
                ext = Extension.fromSpecialVersionTR(exttr, debug=debug)
                if ext:
                    extList.extensions.append(ext)
        return extList

    @classmethod
    def restore(cls) -> "ExtensionList":
        """
        restore the extension list
        """
        path = ExtensionList.storeFilePrefix()
        yaml_file = f"{path}.yaml"
        extlist = ExtensionList.load_from_yaml_file(yaml_file)
        return extlist
