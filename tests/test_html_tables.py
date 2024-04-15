"""
Created on 25.10.2022

@author: wf
"""
import pprint
import unittest

from mwdocker.html_table import HtmlTables
from tests.basetest import Basetest


class TestHtmlTables(Basetest):
    """
    test the HTML Tables parsere
    """

    def testHtmlTables(self):
        url = "https://en.wikipedia.org/wiki/Special:Version"
        html_table = HtmlTables(url)
        tables = html_table.get_tables("h2")
        pp = pprint.PrettyPrinter(indent=2)
        debug = self.debug
        # debug=True
        if debug:
            pp.pprint(tables)
        pass


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
