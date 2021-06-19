'''
Created on 2021-08-06
@author: wf
'''
from mwdocker.dimage import DockerClient,DockerImage

class MediaWikiCluster(object):
    '''
    a cluster of mediawiki 
    '''

    def __init__(self,debug=False,sqlPort=9306,basePort=9080,versions=["1.27.7","1.31.14","1.35.2"],networkName="mwNetwork",mariaDBVersion="10.5",mySQLRootPassword="insecurepassword"):
        '''
        Constructor
        '''
        self.debug=debug
        self.sqlPort=sqlPort
        self.basePort=basePort
        self.versions=versions
        self.mariaDBVersion=mariaDBVersion
        self.mySQLRootPassword=mySQLRootPassword
        self.dockerClient=DockerClient.getInstance()
        self.client=self.dockerClient.client
        # check that docker runs
        self.client.ping()
        # create a network
        self.networkName=networkName
        self.createNetwork()
        self.containers={}
        
    def createNetwork(self):
        '''
        create my network if it does not exist yet
        '''
        self.network=None
        # get the current list of networks
        nlist=self.client.networks.list()
        # if network is available use it
        for network in nlist:
            if network.name==self.networkName:
                self.network=network
                break
        if self.network is None:
            self.network=self.client.networks.create(self.networkName, driver="bridge")
        
    def prepareImages(self):
        '''
        prepare the images
        '''
        self.mariaImage=DockerImage(self.dockerClient,name="mariadb",version=self.mariaDBVersion)
        self.mariaImage.pull()
        self.runContainer(name=self.mariaImage.defaultContainerName(),dockerImage=self.mariaImage,
            environment={"MYSQL_ROOT_PASSWORD":self.mySQLRootPassword},
            network=self.networkName,
            hostname="mariadb",
            ports={'3306/tcp': self.sqlPort}
        )
        for i,version in enumerate(self.versions):
            port=self.basePort+i
            mwImage=DockerImage(self.dockerClient,version=version,debug=True)
            mwImage.pull()
            mwname=version.replace(".","")
            name=mwImage.defaultContainerName()
            self.runContainer(name, mwImage,network=self.networkName,
                ports={'80/tcp': port},
                hostname=f"mw{mwname}"
            )
            
    def runContainer(self,name,dockerImage:DockerImage,**kwArgs):
        '''
        run a container for the given docker image
        '''
        containerMap=self.dockerClient.getContainerMap()
        if name in containerMap:
            container=containerMap[name]
        else:
            container=dockerImage.run(name=name,**kwArgs)
        self.containers[name]=container
    