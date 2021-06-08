'''
Created on 2021-08-06

@author: wf
'''
import docker

class MWImage(object):
    '''
    MediaWiki Docker image
    '''


    def __init__(self,client,version="1.35.2"):
        '''
        Constructor
        '''
        self.client=client
        self.version=version
        
    def pull(self):
        self.client.images.pull('mediawiki',tag=self.version)