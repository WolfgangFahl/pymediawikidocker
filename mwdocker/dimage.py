'''
Created on 2021-08-06

@author: wf
'''
import docker
import distutils.spawn
import os

class DockerClient(object):
    '''
    wrapper for docker library
    '''
    instance=None
    
    def __init__(self):
        self.client = docker.from_env()
        
    def getImageMap(self):
        imageList=self.client.images.list()
        imageMap={}
        for image in imageList:
            imageMap[image.tags[0]]=image
        return imageMap
        
    @classmethod
    def getInstance(cls):
        if cls.instance is None:
            cls.instance=DockerClient()
        return cls.instance
    
    
class DockerImage(object):
    '''
    MediaWiki Docker image
    '''

    def __init__(self,dockerClient=None,name="mediawiki",version="1.35.2",debug=False,doCheckDocker=True):
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
        if doCheckDocker:
            self.checkDocker()
            
    def defaultContainerName(self):
        return f"{self.name}_{self.version}"
    
    def checkCredentialsDesktop(self):
        cmd="docker-credential-desktop"
        path=distutils.spawn.find_executable(cmd)
        return path
    
    def addPath(self,path):
        ospath=os.environ["PATH"]
        if not path in ospath:
            os.environ["PATH"]=f"{ospath}{os.pathsep}{path}"
    
    def checkDocker(self):
        if self.checkCredentialsDesktop() is None:
            self.addPath("/usr/local/bin")
        if self.debug:
            print(os.environ["PATH"])
        
    def pull(self):
        '''
        pull me
        '''
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