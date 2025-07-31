"""
Created on 2022-10-25

@author: wf
"""

from mwdocker.webscrape import WebScrape


class HtmlTables(WebScrape):
    """
    HtmlTables extractor
    """

    def __init__(self, url: str, debug=False, showHtml=False):
        """
        Constructor

        url(str): the url to read the tables from
        debug(bool): if True switch on debugging
        showHtml(bool): if True show the HTML retrieved
        """
        super().__init__(debug, showHtml)
        self.soup = super().getSoup(url, showHtml)

    def get_tables(self, header_tag: str = None) -> dict:
        """
        get all tables from my soup as a list of list of dicts

        Args:
            header_tag(str): if set search the table name from the given header tag

        Return:
            dict: the list of list of dicts for all tables

        """
        tables = {}
        for i, table in enumerate(self.soup.find_all("table")):
            fields = []
            table_data = []
            category = None
            for tr in table.find_all("tr", recursive=True):
                for th in tr.find_all("th", recursive=True):
                    if "colspan" in th.attrs:
                        category = th.text
                    else:
                        fields.append(th.text)
            for tr in table.find_all("tr", recursive=True):
                record = {}
                for i, td in enumerate(tr.find_all("td", recursive=True)):
                    record[fields[i]] = td.text
                if record:
                    if category:
                        record["category"] = category
                    table_data.append(record)
            if header_tag is not None:
                header = table.find_previous_sibling(header_tag)
                table_name = header.text
            else:
                table_name = f"table{i}"
            tables[table_name] = table_data
        return tables
