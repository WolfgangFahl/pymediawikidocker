'''
Created on 2021-08-06

@author: wf
'''
from python_on_whales import docker
import os
import datetime
import secrets
import socket
import re
from jinja2 import Environment, FileSystemLoader
    
class DockerMap():
    @staticmethod
    def getImageMap():
        '''
        '''
        imageMap={}
        for image in docker.image.list():
            pass
        return imageMap
    
class DockerApplication(object):
    '''
    MediaWiki Docker image
    '''

    def __init__(self,name="mediawiki",version="1.35.2",mariaDBVersion="10.5",port=9080,sqlPort=9306,debug=False,verbose=True,doCheckDocker=True):
        '''
        Constructor
        '''
        self.name=name
        self.version=version
        self.mariaDBVersion=mariaDBVersion
        self.port=port
        self.sqlPort=sqlPort
        self.image=None
        self.debug=debug
        self.verbose=verbose
        self.env=self.getJinjaEnv()
  
            
    def defaultContainerName(self):
        '''
        return the default container name which consists of the 
        my name with the version appended
        
        Returns
            str: the default container name
        '''
        return f"{self.name}_{self.version}"
    
            
    def getJinjaEnv(self):
        '''
        get a Jinja2 environment
        '''
        scriptpath=os.path.realpath(__file__)
        resourcePath=os.path.realpath(f"{scriptpath}/../../resources")
        template_dir = os.path.realpath(f'{resourcePath}/templates')
        #print(f"jinja template directory is {template_dir}")
        self.dockerPath=f'{resourcePath}/mw{self.version.replace(".","_")}' 
        os.makedirs(self.dockerPath,exist_ok=True)
        env = Environment(loader=FileSystemLoader(template_dir))
        return env
    
    def generate(self,templateName:str,targetPath:str,**kwArgs):
        '''
        generate file at targetPath using the given templateName
        
        Args:
            templateName(str): the Jinja2 template to use
            targetPath(str): the path to the target file
            kwArgs(): generic keyword arguments to pass on to template rendering
        
        '''
        template = self.env.get_template(templateName)
        timestamp=datetime.datetime.now().isoformat()
        content=template.render(mwVersion=self.version,mariaDBVersion=self.mariaDBVersion,port=self.port,sqlPort=self.sqlPort,timestamp=timestamp,**kwArgs)
        with open(targetPath, "w") as targetFile:
            targetFile.write(content)
      
    def genComposerFile(self,**kwArgs):  
        '''
        generate the composer file for 
        '''
        password_length = 13
        password=secrets.token_urlsafe(password_length)
        self.generate("mwCompose.yml",f"{self.dockerPath}/docker-compose.yml",mySQL_Password=password,**kwArgs)       
        
        
    def genDockerFile(self,**kwArgs):
        '''
        generate the docker files for this cluster
        '''
        self.generate("mwDockerfile",f"{self.dockerPath}/Dockerfile",**kwArgs)
        
    def genLocalSettings(self,**kwArgs):
        '''
        generate the local settings file
        '''
        hostname=socket.getfqdn()
        versionMatch=re.match("(?P<major>[0-9]+)\.(?P<minor>[0-9]+)",self.version)
        shortVersion=f"{versionMatch.group('major')}{versionMatch.group('minor')}"
        self.generate(f"mwLocalSettings{shortVersion}.php",f"{self.dockerPath}/LocalSettings.php",hostname=hostname,**kwArgs)
    
    def up(self):
        '''
        
        '''
        if self.verbose:
            print(f"starting {self.name} {self.version} docker application ...")
        # change directory so that docker CLI will find the relevant dockerfile and docker-compose.yml
        os.chdir(self.dockerPath)
        # run docker compose up
        docker.compose.up(detach=True)
            
