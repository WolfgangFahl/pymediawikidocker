"""
Created on 2025-08-01

@author: wf
"""

import sys
from argparse import ArgumentParser, Namespace

from basemkit.base_cmd import BaseCmd

from mwdocker.config import MwClusterConfig, MwConfig
from mwdocker.mwcluster import MediaWikiCluster
from mwdocker.version import Version


class MediaWikiDockerCmd(BaseCmd):
    """
    pymediawiki docker main
    """

    def __init__(self, version=Version):
        super().__init__(version)
        self.config = MwClusterConfig()
        self.cluster = None

    def getMwConfig(self, argv=None, version=None) -> MwClusterConfig:
        """
        get a mediawiki configuration for the given command line arguments
        """
        if not argv:
            argv = self.argv
        parser = ArgumentParser()
        if version is None:
            version = MwConfig.version
        mwClusterConfig = MwClusterConfig(version=version)
        self.config = mwClusterConfig
        self.add_arguments(parser)
        args = parser.parse_args(argv)
        mwClusterConfig.fromArgs(args)
        return mwClusterConfig

    def add_arguments(self, parser: ArgumentParser):
        """
        add parser arguments
        """
        super().add_arguments(parser)
        self.config.addArgs(parser)
        parser.add_argument("--create", action="store_true")
        parser.add_argument("--down", action="store_true")
        parser.add_argument("--check", action="store_true")
        parser.add_argument("--list", action="store_true")

    def handle_args(self, args: Namespace) -> bool:
        if super().handle_args(args):
            return True
        self.config.fromArgs(args)
        self.cluster = MediaWikiCluster(self.config,args)
        self.cluster.createApps(withGenerate=args.create)
        if args.check:
            self.exit_code = self.cluster.check()
        elif args.create:
            self.exit_code = self.cluster.start(forceRebuild=self.config.forceRebuild)
        elif args.list:
            self.exit_code = self.cluster.listWikis()
        elif args.down:
            self.exit_code = self.cluster.down(forceRebuild=self.config.forceRebuild)
        else:
            self.parser.print_usage()
            self.exit_code = 1
        return True


def main(argv=None):
    return MediaWikiDockerCmd.main(version=Version, argv=argv)


if __name__ == "__main__":
    sys.exit(main())
