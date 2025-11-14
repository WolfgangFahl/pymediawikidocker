"""
Created on 2023-04-06

@author: wf
"""

import dataclasses
import json
import os
import re
import secrets
import socket
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from basemkit.yamlable import lod_storable
from lodstorage.lod import LOD

from mwdocker.mw import ExtensionList
from mwdocker.docker_map import DockerMap

class Host:
    """
    Host name getter
    """

    @classmethod
    def get_default_host(cls) -> str:
        """
        Get the default host as a usable hostname or IP,
        never returning reverse-DNS PTRs and avoiding localhost which
        might cause to try socket access instead of proper host access
        """
        host = socket.getfqdn()

        # work around https://github.com/python/cpython/issues/79345
        if host == (
            "1.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.0.ip6.arpa"
        ):
            host = "127.0.0.1"

        elif host.endswith(".in-addr.arpa"):
            host = "127.0.0.1"

        elif host.endswith(".ip6.arpa"):
            host = "::1"

        elif host == "localhost":
            host = "127.0.0.1"

        return host



@lod_storable
class MwConfig:
    """
    MediaWiki and docker configuration for a Single Wiki
    """
    version: str = "1.39.15"
    smw_version: Optional[str] = None
    extensionNameList: Optional[List[str]] = field(
        default_factory=lambda: [
            "Admin Links",
            "Header Tabs",
            "ParserFunctions",
            "SyntaxHighlight",
            "Variables",
        ]
    )
    extensionJsonFile: Optional[str] = None
    user: str = "Sysop"
    prefix: str = "mw"
    logo: str = "$wgResourceBasePath/resources/assets/wiki.png"
    url = None
    full_url = None
    prot: str = "http"
    host: str = Host.get_default_host()
    article_path: Optional[str] = None  # "/index.php/$1"
    script_path: str = ""
    wikiId: Optional[str] = None
    # mysql settings
    mySQLRootPassword: Optional[str] = None
    mySQLPassword: Optional[str] = None
    mariaDBVersion: str = "11.4"

    # docker settings
    bind_mount: bool = False
    port: int = 9080
    base_port: Optional[int] = None
    sql_port: int = 9306
    container_base_name: Optional[str] = None
    # derived from container_base_name if different than default
    # an external db_container is going to be used
    db_container_name: Optional[str] = None
    networkName: str = "mwNetwork"
    docker_path: Optional[str] = None
    gid: int = 33  # www-data
    uid: int = 33  # www-data

    # build control
    verbose: bool = True
    random_password: bool = False
    force_user: bool = False
    lenient: bool = True
    password_length: int = 15
    forceRebuild: bool = False
    debug: bool = False
    # FIXME - we should avoid a predefined known password
    password: str = "sysop-1234!"

    def default_docker_path(self) -> str:
        """
        get the default docker path

        Returns:
            str: $HOME/.pymediawikidocker
        """
        home = str(Path.home())
        docker_path = f"{home}/.pymediawikidocker"
        return docker_path

    def __post_init__(self):
        """
        post initialization configuration
        """
        self.fullVersion = f"MediaWiki {self.version}"
        self.underscoreVersion = self.version.replace(".", "_")
        self.shortVersion = self.getShortVersion()
        if not self.docker_path:
            self.docker_path = self.default_docker_path()
        if not self.container_base_name:
            self.container_base_name = f"{self.prefix}-{self.shortVersion}"
        if not self.db_container_name:
            self.db_container_name = f"{self.container_base_name}-db"
        if not self.article_path:
            self.article_path = ""
        if not self.base_port:
            self.base_port = self.port
        self.reset_url(self.url)

    @property
    def has_external_db(self) -> bool:
        """
        Check if using external database container

        Returns:
            bool: True if db_container_name differs from default pattern
        """
        default_db_name = f"{self.container_base_name}-db"
        external= self.db_container_name != default_db_name
        return external

    def reset_url(self, url: str):
        """
        reset my url

        Args:
            url(str): the url to set
        """
        if url:
            pr = urlparse(url)
            self.prot = pr.scheme
            self.host = pr.hostname
            self.script_path = pr.path
            self.base_url = f"{self.prot}://{self.host}"
            self.full_url = url
        else:
            self.base_url = f"{self.prot}://{self.host}:{self.base_port}"

            self.full_url = f"{self.base_url}{self.script_path}"

    def reset_container_base_name(self, container_base_name: str=None):
        """
        reset the container base name to the given name

        Args:
            container_base_name(str): the new container base name
        """
        self.container_base_name = container_base_name
        self.__post_init__()

    def as_dict(self) -> dict:
        """
        return my fields as a dict
        dataclasses to dict conversion convenienc and information hiding

        Returns:
            dict: my fields in dict format
        """
        config_dict = dataclasses.asdict(self)
        return config_dict

    def as_json(self) -> str:
        """
        return me as a json string

        Returns:
            str: my json representation
        """
        config_dict = self.as_dict()
        json_str = json.dumps(config_dict, indent=2)
        return json_str

    def get_config_path(self) -> str:
        """
        get my configuration base path

        Returns:
            str: the path to my configuration
        """
        config_base_path = f"{self.docker_path}/{self.container_base_name}"
        os.makedirs(config_base_path, exist_ok=True)
        path = f"{config_base_path}/MwConfig.json"
        return path

    def save(self, path: str=None) -> str:
        """
        save my json

        Args:
            path(str): the path to store to - if None use {docker_path}/{container_base_name}/MwConfig.json
        Returns:
            str: the path
        """
        if path is None:
            path = self.get_config_path()

        json_str = self.as_json()
        with open(path, "w") as f:
            print(json_str, file=f)
        return path

    def load(self, path: str=None) -> "MwConfig":
        """
        load the the MwConfig from the given path of if path is None (default)
        use the config_path for the current configuration

        restores the ExtensionMap on load

        Args:
            path(str): the path to load from

        Returns:
            MwConfig: a MediaWiki Configuration
        """
        if path is None:
            path = self.get_config_path()
        with open(path, "r") as json_file:
            json_str = json_file.read()
            config = self.__class__.from_json(json_str)
            # restore extension map
            config.getExtensionMap(config.extensionNameList, config.extensionJsonFile)
            return config

    def getShortVersion(self, separator=""):
        """
        get my short version e.g. convert 1.27.7 to 127

        Returns:
            str: the short version string
        """
        versionMatch = re.match(r"(?P<major>[0-9]+)\.(?P<minor>[0-9]+)", self.version)
        shortVersion = (
            f"{versionMatch.group('major')}{separator}{versionMatch.group('minor')}"
        )
        return shortVersion

    def create_random_password(self, length: int=15) -> str:
        """
        create a random password

        Args:
            length(int): the length of the password

        Returns:
            str:a random password with the given length
        """
        random_password = secrets.token_urlsafe(length)
        return random_password

    def getWikiId(self):
        """
        get the wikiId

        Returns:
            str: e.g. mw-9080
        """
        if self.wikiId is None:
            wikiId = f"{self.prefix}-{self.port}"
        else:
            wikiId = self.wikiId
        return wikiId

    def getExtensionMap(
        self, extensionNameList: list=None, extensionJsonFile: str=None
    ):
        """
        get map of extensions to handle

        Args:
            extensionNameList (list): a list of extension names
            extensionJsonFile (str): the name of an extra extensionJsonFile (if any)
        """
        self.extensionMap = {}
        extensionList = ExtensionList.restore()
        self.extByName, duplicates = LOD.getLookup(extensionList.extensions, "name")
        if len(duplicates) > 0:
            print(f"{len(duplicates)} duplicate extensions: ")
            for duplicate in duplicates:
                print(duplicate.name)
        if extensionJsonFile is not None:
            extraExtensionList = ExtensionList.load_from_json_file(extensionJsonFile)  # @UndefinedVariable
            for ext in extraExtensionList.extensions:
                if ext.name in self.extByName:
                    print(f"overriding {ext.name} extension definition")
                self.extByName[ext.name] = ext
        if extensionNameList is not None:
            self.addExtensions(extensionNameList)
        return self.extensionMap

    def addExtensions(self, extensionNameList):
        """
        add extensions for the given list of extension names
        """
        for extensionName in extensionNameList:
            if extensionName in self.extByName:
                self.extensionMap[extensionName] = self.extByName[extensionName]
            else:
                print(f"warning: extension {extensionName} not known")

    def fromArgs(self, args):
        """
        initialize me from the given commmand line arguments

        Args:
            args(Namespace): the command line arguments
        """
        self.prefix = args.prefix
        self.article_path = args.article_path
        self.container_base_name = args.container_name
        self.db_container_name = args.db_container_name
        self.docker_path = args.docker_path
        self.extensionNameList = args.extensionNameList
        self.extensionJsonFile = args.extensionJsonFile
        self.bind_mount = args.bind_mount
        self.uid = args.uid
        self.gid = args.gid
        self.forceRebuild = args.forceRebuild or getattr(args, "force", False)
        self.host = args.host
        self.logo = args.logo
        self.mariaDBVersion = args.mariaDBVersion
        # passwords
        if args.mysqlRootPassword:
            self.mySQLRootPassword = args.mysqlRootPassword
        if not self.mySQLRootPassword:
            if args.db_container_name:
                # we need the password from the database container
                pass
            else:
                self.mySQLRootPassword = self.create_random_password(self.password_length)
        if args.mysqlPassword:
            self.mySQLPassword = args.mysqlPassword
        else:
            self.mySQLPassword = self.create_random_password(self.password_length)
        self.prot = args.prot
        self.script_path = args.script_path
        self.versions = args.versions
        self.user = args.user
        self.random_password = args.random_password
        self.force_user = args.force_user
        self.lenient = args.lenient
        self.password = args.password
        self.password_length = args.password_length
        self.base_port = args.base_port
        self.sql_port = args.sql_port
        self.smw_version = args.smw_version
        self.verbose = not args.quiet
        self.debug = args.debug
        self.getExtensionMap(self.extensionNameList, self.extensionJsonFile)
        self.reset_url(args.url)

    def addArgs(self, parser):
        """
        add Arguments to the given parser
        """
        parser.add_argument(
            "--article_path",
            default=self.article_path,
            help="change to any article_path you might need to set [default: %(default)s]",
        )
        parser.add_argument(
            "-bm",
            "--bind-mount",
            action="store_true",
            help="use bind mounts instead of volumes",
        )
        parser.add_argument(
            "-cn",
            "--container_name",
            default=self.container_base_name,
            help="set container name (only valid and recommended for single version call)",
        )
        parser.add_argument(
            "-dcn",
            "--db_container_name",
            help="set database container name [default: %(default)s]",
        )
        parser.add_argument(
            "-el",
            "--extensionList",
            dest="extensionNameList",
            nargs="*",
            default=self.extensionNameList,
            help="list of extensions to be installed [default: %(default)s]",
        )
        parser.add_argument(
            "-ej",
            "--extensionJson",
            dest="extensionJsonFile",
            default=self.extensionJsonFile,
            help="additional extension descriptions default: [default: %(default)s]",
        )
        # since -f is a default options we have to make sure we accept it as forceRebuild
        parser.add_argument(
            "--forceRebuild",
            action="store_true",
            default=self.forceRebuild,
            help="force rebuilding  [default: %(default)s]",
        )
        parser.add_argument(
            "-fu",
            "--force_user",
            action="store_true",
            default=self.force_user,
            help="force overwrite of wikiuser",
        )
        parser.add_argument(
            "--host",
            default=Host.get_default_host(),
            help="the host to serve / listen from [default: %(default)s]",
        )
        parser.add_argument(
            "-dp",
            "--docker_path",
            default=self.default_docker_path(),
            help="the base directory to store docker and jinja template files [default: %(default)s]",
        )
        parser.add_argument(
            "--lenient",
            action="store_true",
            help="do not throw error on wikiuser difference",
        )
        parser.add_argument(
            "--logo", default=self.logo, help="set Logo [default: %(default)s]"
        )
        parser.add_argument(
            "-mv",
            "--mariaDBVersion",
            dest="mariaDBVersion",
            default=self.mariaDBVersion,
            help="mariaDB Version to be installed [default: %(default)s]",
        )
        parser.add_argument(
            "--mysqlRootPassword",
            default=self.mySQLRootPassword,
            help="set sql root Password [default: %(default)s] - random password if None",
        )
        parser.add_argument(
            "--mysqlPassword",
            default=self.mySQLPassword,
            help="set sql user Password [default: %(default)s] - random password if None",
        )
        parser.add_argument(
            "-rp",
            "--random_password",
            action="store_true",
            default=self.random_password,
            help="create random password and create wikiuser while at it",
        )
        parser.add_argument(
            "-p",
            "--password",
            dest="password",
            default=self.password,
            help="set password for initial user [default: %(default)s] ",
        )
        parser.add_argument(
            "-pl",
            "--password_length",
            default=self.password_length,
            help="set the password length for random passwords[default: %(default)s] ",
        )
        parser.add_argument(
            "--prefix",
            default=self.prefix,
            help="the container name prefix to use [default: %(default)s]",
        )
        parser.add_argument(
            "--prot",
            default=self.prot,
            help="change to https in case [default: %(default)s]",
        )
        parser.add_argument(
            "--script_path",
            default=self.script_path,
            help="change to any script_path you might need to set [default: %(default)s]",
        )
        parser.add_argument(
            "--url",
            default=self.url,
            help="will set prot host,script_path, and optionally port based on the url given [default: %(default)s]",
        )
        parser.add_argument(
            "-sp",
            "--sql_base_port",
            dest="sql_port",
            type=int,
            default=self.sql_port,
            help="set base mySql port 3306 to be exposed - incrementing by one for each version [default: %(default)s]",
        )
        parser.add_argument(
            "-smw",
            "--smw_version",
            dest="smw_version",
            default=self.smw_version,
            help="set SemanticMediaWiki Version to be installed default is None - no installation of SMW",
        )
        parser.add_argument(
            "-u",
            "--user",
            dest="user",
            default=self.user,
            help="set username of initial user with sysop rights [default: %(default)s] ",
        )
        parser.add_argument("--uid", type=int, default=self.uid, help="User ID  (default: 33 for www-data)")
        parser.add_argument("--gid", type=int, default=self.gid, help="Group ID (default: 33 for www-data)")


@dataclass
class MwClusterConfig(MwConfig):
    """
    MediaWiki Cluster configuration for multiple wikis
    """

    versions: Optional[List[str]] = field(
        default_factory=lambda: ["1.35.13", "1.39.15", "1.43.5", "1.44.2"]
    )
    base_port: int = 9080

    def addArgs(self, parser):
        """
        add my arguments to the given parser
        """
        super().addArgs(parser)
        parser.add_argument(
            "-bp",
            "--base_port",
            dest="base_port",
            type=int,
            default=self.base_port,
            help="set how base html port 80 to be exposed - incrementing by one for each version [default: %(default)s]",
        )
        parser.add_argument(
            "-vl",
            "--version_list",
            dest="versions",
            nargs="*",
            default=self.versions,
            help="mediawiki versions to create docker applications for [default: %(default)s] ",
        )

    def fromArgs(self, args):
        """
        initialize me from the given commmand line arguments

        Args:
            args(Namespace): the command line arguments
        """
        dbc_name=args.db_container_name
        if dbc_name:
            env=DockerMap.getEnv(dbc_name)
            self.mySQLRootPassword=env["MYSQL_ROOT_PASSWORD"]
            pass
        super().fromArgs(args)
