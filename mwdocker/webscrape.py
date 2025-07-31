"""
Created on 2020-08-20

@author: wf
"""

from urllib.request import Request, urlopen

from bs4 import BeautifulSoup


class WebScrape(object):
    """
    WebScraper
    """

    def __init__(self, debug=False, showHtml=False):
        """
        Constructor
        """
        self.err = None
        self.valid = False
        self.debug = debug
        self.showHtml = showHtml

    def getSoup(self, url, showHtml):
        """
        get the beautiful Soup parser

        Args:
           showHtml(boolean): True if the html code should be pretty printed and shown
        """
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        html = urlopen(req).read()
        soup = BeautifulSoup(html, "html.parser", from_encoding="utf-8")
        if showHtml:
            self.printPrettyHtml(soup)

        return soup

    def printPrettyHtml(self, soup):
        """
        print the prettified html for the given soup

        Args:
            soup(BeuatifulSoup): the parsed html to print
        """
        prettyHtml = soup.prettify()
        print(prettyHtml)
