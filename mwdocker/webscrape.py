"""
Created on 2020-08-20

@author: wf
"""

from urllib.request import Request, urlopen

from bs4 import BeautifulSoup

from mwdocker import __version__


class WebScrape(object):
    """
    WebScraper
    """

    def __init__(
        self, debug: bool = False, showHtml: bool = False, timeout: float = 20.0
    ):
        """
        Constructor

        Args:
            debug: if True show debugging information
            showHtml: if True show the html retrieved
            timeout: socket timeout in seconds for url requests
        """
        self.err = None
        self.valid = False
        self.debug = debug
        self.showHtml = showHtml
        self.timeout = timeout

    def getSoup(self, url, showHtml):
        """
        get the beautiful Soup parser

        Args:
           showHtml(boolean): True if the html code should be pretty printed and shown
        """
        # honest tool user agent: fake browser agents are challenged by
        # anti-bot proxies (e.g. Anubis on the BITPlan wikis) while an empty
        # agent is rejected by the Wikimedia user agent policy
        user_agent = f"pymediawikidocker/{__version__} (+https://github.com/WolfgangFahl/pymediawikidocker)"
        req = Request(url, headers={"User-Agent": user_agent})
        html = urlopen(req, timeout=self.timeout).read()
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
