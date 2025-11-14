"""
Created on 2021-08-06
@author: wf
"""

from argparse import Namespace
import dataclasses
import sys

from mwdocker.config import MwClusterConfig
from mwdocker.docker import DockerApplication
from mwdocker.logger import Logger


class MediaWikiCluster(object):
    """
    a cluster of mediawiki docker Applications
    """

    # https://hub.docker.com/_/mediawiki
    # 2023-01-13
    # MediaWiki Extensions and Skins Security Release Supplement (1.35.9/1.38.4/1.39.1)
    # 2023-02-23 1.39.2 released
    # 2023-04-04 1.39.3 upgrade
    # 2023-10-04 1.39.5 upgrade
    # 2024-04-15 1.39.7 upgrade
    # 2024-08-02 1.39.8 upgrade
    # 2024-10-11 1.39.10 upgrade
    # 2025-03-18 1.39.11 upgrade 1.43.0 addition
    # 2025-04-13 Security and maintenance release: 1.39.12 / 1.42.6 / 1.43.1
    # 2025-06-30 Security and maintenance release: 1.39.13 / 1.42.7 / 1.43.3
    # 2025-10-05 Security and maintenance release: 1.39.14 / 1.43.4 / 1.44.1
    # 2025-11-14 Security and maintenance release: 1.39.15 / 1.43.5 / 1.44.2

    def __init__(self, config: MwClusterConfig,args:Namespace=None):
        """
        Constructor

        Args:
            config(MWClusterConfig): the MediaWiki Cluster Configuration to use
        """
        self.config = config
        self.args=args
        self.apps = {}

    def createApps(self, withGenerate: bool = True) -> dict:
        """
        create my apps

        Args:
            withGenerate(bool): if True generate the config files

        Returns:
            dict(str): a dict of apps by version
        """
        exitCode = self.checkDocker()
        if exitCode > 0:
            raise ValueError("createApps needs docker command in PATH")
        app_count = len(self.config.versions)
        for i, version in enumerate(self.config.versions):
            mwApp = self.getDockerApplication(i, app_count, version)
            if withGenerate:
                mwApp.generateAll(overwrite=self.config.forceRebuild)
            self.apps[version] = mwApp
        return self.apps

    def checkDocker(self) -> int:
        """
        check the Docker environment

        print an error message on stderr if check fails

        Returns:
            int: exitCode - 0 if ok 1 if failed

        """
        errMsg = DockerApplication.checkDockerEnvironment(self.config.debug)
        if errMsg is not None:
            print(errMsg, file=sys.stderr)
            return 1
        return 0

    def start(self, forceRebuild: bool = False, withInitDB=True) -> int:
        """
        create and start the composer applications

        Returns:
            int: exitCode - 0 if ok 1 if failed
        """
        exitCode = self.checkDocker()
        if exitCode > 0:
            return exitCode

        for version in self.config.versions:
            mwApp = self.apps[version]
            mwApp.start(forceRebuild=forceRebuild, withInitDB=withInitDB)
        return 0

    def down(self, forceRebuild: bool = False):
        """
        run docker compose down
        """
        exitCode = self.checkDocker()
        if exitCode > 0:
            return exitCode
        for _i, version in enumerate(self.config.versions):
            mwApp = self.apps[version]
            mwApp.down(forceRebuild)

    def listWikis(self) -> int:
        """
        list my wikis

        Returns:
            int: exitCode - 0 if ok 1 if failed
        """
        exitCode = self.checkDocker()
        if exitCode > 0:
            return exitCode
        for i, version in enumerate(self.config.versions):
            mwApp = self.apps[version]
            mw, db = mwApp.getContainers()
            config = mwApp.config
            ok = mw and db
            msg = f"{i+1}:{config.container_base_name} {config.fullVersion}"
            Logger.check_and_log(msg, ok)
        return exitCode

    def check(self) -> int:
        """
        check the composer applications

        Returns:
            int: exitCode - 0 if ok 1 if failed
        """
        exitCode = self.checkDocker()
        if exitCode > 0:
            return exitCode

        for i, version in enumerate(self.config.versions):
            mwApp = self.apps[version]
            msg = f"{i+1}:checking {version} ..."
            print(msg)
            exitCode = mwApp.check()
        return exitCode

    def close(self):
        """
        close my apps
        """
        for mwApp in self.apps.values():
            mwApp.close()

    def getDockerApplication(self, i: int, count: int, version: str):
        """
        get the docker application for the given version index and version

        Args:
            i(int): the index of the version
            count(int): total number of Docker applications in this cluster
            version(str): the mediawiki version to use

        Returns:
            DockerApplication: the docker application
        """
        # please note that we are using the subclass MwClusterConfig here although
        # we only need the superclass MwConfig - we let inheritance work here for us but
        # have to ignore the superfluous fields
        appConfig = dataclasses.replace(self.config)
        appConfig.extensionMap = self.config.extensionMap.copy()
        appConfig.version = version
        appConfig.base_port = self.config.base_port + i
        appConfig.port = self.config.base_port + i
        appConfig.sql_port = self.config.sql_port + i
        # let post_init create a new container_base_name and db_container_name
        if count > 1:
            appConfig.container_base_name = None
            appConfig.db_container_name = self.args.db_container_name if self.args else None
        appConfig.__post_init__()
        mwApp = DockerApplication(config=appConfig)
        return mwApp
