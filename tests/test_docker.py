"""
Created on 2025-07-31

@author: wf
"""

from basemkit.basetest import Basetest
from python_on_whales import docker

from mwdocker.docker import DockerApplication, DockerContainer


class TestDocker(Basetest):
    """
    test the docker handling
    """

    def setUp(self, debug=False, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        DockerApplication.checkDockerEnvironment(debug)

    def testDockerState(self):
        """
        test docker state checking and waiting
        """
        # Run a simple ash loop in busybox to test scripting support
        imax=3
        if self.inPublicCI():
            imax=10
        for i in range(1, imax):
            with self.subTest(sleep=i):
                container_name = f"busybox-sleep-{i}"
                # Ensure stale container is removed
                if docker.container.exists(container_name):
                    docker.container.remove(container_name, force=True)
                container = docker.container.run(
                    "busybox",
                    ["sh", "-c", f"sleep {i}; echo 'slept {i}s'"],
                    detach=True,
                    name=container_name,
                    remove=False,
                )
                dc = DockerContainer(
                    name=container_name, kind="test", container=container
                )
                start_secs = dc.wait_for_state(running=True)
                print(f"{container_name} 🟢 started in {start_secs:.2f}s")
                stop_secs = dc.wait_for_state(running=False)
                print(f"{container_name} 🔴 stopped after {stop_secs:.2f}s")
                self.assertGreaterEqual(stop_secs, i)
                logs = docker.container.logs(container_name)
                self.assertIn(f"slept {i}s", logs)
                docker.container.remove(container_name, force=True)
