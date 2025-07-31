"""
Created on 2022-10-25

@author: wf
"""

import pprint

from basemkit.basetest import Basetest

from mwdocker.html_table import HtmlTables


class TestHtmlTables(Basetest):
    """
    test the HTML Tables parsere
    """

    def testHtmlTables(self):
        urls = [
            "https://wiki.bitplan.com/index.php/Special:Version",
            "https://en.wikipedia.org/wiki/Special:Version",
        ]
        for url in urls:
            html_table = HtmlTables(url)
            tables = html_table.get_tables("h2")
            pp = pprint.PrettyPrinter(indent=2)
            debug = self.debug
            # debug=True
            if debug:
                pp.pprint(tables)
            self.assertTrue("Installed extensions" in tables)
            pass
