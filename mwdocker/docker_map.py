'''
Created on 2025-08-21

@author: wf
'''
from typing import Dict

from python_on_whales import docker
from python_on_whales.components.container.cli_wrapper import Container


class DockerMap:
    """
    helper class to convert lists of docker elements to maps for improved
    lookup functionality
    """

    _container_map = None

    @classmethod
    def getContainer(cls,container_name:str):
        containerMap = DockerMap.getContainerMap()
        if not container_name in containerMap:
            raise ValueError(f"container {container_name} is not a valid docker container")
        container=containerMap.get(container_name)
        return container

    @classmethod
    def getEnv(cls,container_name:str)->Dict[str,str]:
        container=cls.getContainer(container_name)
        env_dict = {}
        env_list=container.config.env
        for key_value in env_list:
            if '=' in key_value:
                key, value = key_value.split('=', 1)
                env_dict[key] = value
        return env_dict

    @staticmethod
    def getContainerMap(force_refresh: bool = True)->Dict[str,Container]:
        """
        get a cached map/dict of containers by container name

        Args:
            force_refresh: if True, refresh from docker instead of using cache
        """
        if DockerMap._container_map is None or force_refresh:
            DockerMap._container_map = {}
            for container in docker.container.list():
                DockerMap._container_map[container.name] = container
        return DockerMap._container_map