'''
Created on 2021-08-06

@author: wf
'''
import docker
import distutils.spawn
import os
from jinja2 import Environment, FileSystemLoader

class DockerClient(object):
    '''
    wrapper for docker library
    '''
    instance=None
    
    def __init__(self):
        self.client = docker.from_env()
        
    def getImageMap(self):
        '''
        get a map/dict of images by firstTag
        
        Returns:
            dict: a map of images by first Tag
        '''
        imageList=self.client.images.list()
        imageMap={}
        for image in imageList:
            if len(image.tags)>0:
                firstTag=image.tags[0]
                imageMap[firstTag]=image
        return imageMap
    
    def getContainerMap(self):
        '''
        get a map of running containers for this image
        
        Returns:
            dict: a map of containers by name
        '''
        containerMap={}
        for container in self.client.containers.list():
            containerMap[container.name]=container
        return containerMap
        
    @classmethod
    def getInstance(cls):
        if cls.instance is None:
            cls.instance=DockerClient()
        return cls.instance
    
    
class DockerImage(object):
    '''
    MediaWiki Docker image
    '''

    def __init__(self,dockerClient=None,name="mediawiki",version="1.35.2",debug=False,verbose=True,doCheckDocker=True):
        '''
        Constructor
        '''
        if dockerClient is None:
            self.dockerClient=DockerClient.getInstance()
        else:
            self.dockerClient=dockerClient
        self.name=name
        self.version=version
        self.image=None
        self.debug=debug
        self.verbose=verbose
        if doCheckDocker:
            self.checkDocker()
            
    def defaultContainerName(self):
        '''
        return the default container name which consists of the 
        my name with the version appended
        
        Returns
            str: the default container name
        '''
        return f"{self.name}_{self.version}"
    
    def checkCredentialsDesktop(self):
        cmd="docker-credential-desktop"
        path=distutils.spawn.find_executable(cmd)
        return path
    
    def addPath(self,path):
        '''
        add the given path to the operating system PATH
        
        Args:
            path(str): the path to add
        '''
        ospath=os.environ["PATH"]
        if not path in ospath:
            os.environ["PATH"]=f"{ospath}{os.pathsep}{path}"
    
    def checkDocker(self):
        '''
        check docker 
            make sure docker-credential-desktop is in operating
            system PATH
        '''
        if self.checkCredentialsDesktop() is None:
            self.addPath("/usr/local/bin")
        if self.debug:
            print(os.environ["PATH"])
            
        
    def genDockerFile(self,**kwArgs):
        '''
        generate the docker files for this cluster
        '''
        scriptpath=os.path.realpath(__file__)
        resourcePath=os.path.realpath(f"{scriptpath}/../../resources")
        template_dir = os.path.realpath(f'{resourcePath}/templates')
        print(f"jinja template directory is {template_dir}")
        self.dockerPath=f'{resourcePath}/mw{self.version.replace(".","_")}'
        self.dockerFilePath=f"{self.dockerPath}/Dockerfile"
        os.makedirs(self.dockerPath,exist_ok=True)
        env = Environment(loader=FileSystemLoader(template_dir))
        template = env.get_template("mwDockerfile")
        dockerFileContent=template.render(mwVersion=self.version,**kwArgs)
        with open(self.dockerFilePath, "w") as dockerFile:
            dockerFile.write(dockerFileContent)
    
    def build(self):
        '''
        build me and return my image
        
        Returns:
            Docker image
        '''
        if self.verbose:
            print(f"building {self.name} {self.version} docker image ...")
        self.image,tee=self.dockerClient.client.images.build(path=self.dockerPath,dockerfile=self.dockerFilePath,tag=self.version)
        return self.image
            
    
    def pull(self):
        '''
        pull me and return my image
        
        Returns:
            Docker image
        '''
        if self.verbose:
            print(f"pulling {self.name} {self.version} docker image ...")
        self.image=self.dockerClient.client.images.pull(self.name,tag=self.version)
        return self.image
        
    def run(self,**kwargs):
        '''
        run this image in a container
        '''
        if self.image is None:
            raise "No image initialized - you might want to e.g. pull one"
        if self.debug:
            print(f"running container for {self.image.tags[0]}")
        container=self.dockerClient.client.containers.run(self.image.id,detach=True,**kwargs)
        return container