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

    def setUp(self, debug=True, profile=True):
        Basetest.setUp(self, debug=debug, profile=profile)
        DockerApplication.checkDockerEnvironment(debug)

    def testDockerState(self):
        """
        test docker state checking and waiting
        """
        # Run a simple ash loop in busybox to test scripting support
        imax = 3
        if self.inPublicCI():
            imax = 10
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

    def testBusyboxCrash(self):
        """test container crash detection"""
        crash_methods = [
            # Method 1: Kill current shell process
            ["sh", "-c", "sleep 1; kill -9 $$"],
            # Method 2: Exit with error code
            ["sh", "-c", "sleep 1; exit 1"],
            # Method 3: SIGKILL self
            ["sh", "-c", "sleep 1; kill -KILL $$"],
            # Method 4: SIGSEGV self
            ["sh", "-c", "sleep 1; kill -SEGV $$"],
            # Method 5: Invalid memory access (if available)
            ["sh", "-c", "sleep 1; kill -ABRT $$"],
        ]

        for i, crash_cmd in enumerate(crash_methods):
            with self.subTest(crash_method=i):
                container_name = f"busybox-crash-{i}"

                if docker.container.exists(container_name):
                    docker.container.remove(container_name, force=True)

                container = docker.container.run(
                    "busybox",
                    crash_cmd,
                    detach=True,
                    name=container_name,
                    remove=False,
                )

                dc = DockerContainer(
                    name=container_name, kind="crash-test", container=container
                )

                # Wait for it to start
                start_secs = dc.wait_for_state(running=True)
                print(f"{container_name} 🟢 started in {start_secs:.2f}s")

                # Wait for crash
                stop_secs = dc.wait_for_state(running=False)
                print(f"{container_name} 🔥 crashed after {stop_secs:.2f}s")

                # Capture and print crash logs
                crash_logs = dc.detect_crash()
                if crash_logs is not None:
                    print(f"💥 Crash logs for method {i}:\n{crash_logs}")
                    crashed = True
                else:
                    crashed = False

            # self.assertTrue(crashed, f"Crash method {i} {crash_cmd} should have detected crash")
            docker.container.remove(container_name, force=True)
