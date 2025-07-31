"""
Created on 2022-10-25

@author: wf
"""

import re


class MariaDB:
    """
    Maria DB handling
    """

    @classmethod
    def getVersion(cls, versionStr: str) -> str:
        """
        get the version from the version String

        Args:
            versionStr(str): the version string to check

        Return:
            str: the extracted version
        """
        # version is anything which is not a dot at beginning
        # two times may be ending with dash
        version_match = re.search(r"([^.]+[.]+[^.-]+)", versionStr)
        version = "?"
        if version_match:
            version = version_match.group(1)
        return version
