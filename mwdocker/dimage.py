'''
Created on 2021-08-06

@author: wf
'''
import docker
import distutils.spawn
import os

class DockerImage(object):
    '''
    MediaWiki Docker image
    '''


    def __init__(self,client,name="mediawiki",version="1.35.2",debug=False,doCheckDocker=True):
        '''
        Constructor
        '''
        self.client=client
        self.name=name
        self.version=version
        self.debug=debug
        if doCheckDocker:
            self.checkDocker()
    
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
        self.client.images.pull(self.name,tag=self.version)