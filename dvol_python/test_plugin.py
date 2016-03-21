"""
Tests for dvol docker integration.

Assumes that:
* we have docker running and are running as root or a user in the docker group
* we have dvol under test installed in /usr/local/bin (as per Makefile)
* we have dvol docker plugin installed and running
* we are not running in parallel with ourselves
* we have access to ports on the machine
* it's totally cool to destroy dvol volumes with certain names (including but
  not limited to memorydiskserver)
* there are no dvol volumes on the machine
"""

import json
import random
import sys
import os

import socket
import subprocess

from twisted.trial.unittest import TestCase
from twisted.python.filepath import FilePath
from testtools import (
    get, docker_host, try_until, run, skip_if_go_version,
    skip_if_python_version, skip_if_docker_version_less_than
)

DVOL = "/usr/local/bin/dvol"


def dvol(args):
    return run([DVOL] + args)


def async_docker(args, stdout, stderr):
    return subprocess.Popen(
        ["docker"] + args,
        stdout=stdout, stderr=stderr,
    )


class VoluminousTests(TestCase):
    def setUp(self):
        self.tmpdir = FilePath(self.mktemp())
        self.tmpdir.makedirs()

    def cleanup_memorydiskserver(self):
        """
        Standard cleanup for memorydiskserver.
        """
        def cleanup():
            try:
                run(["docker", "rm", "-f", "memorydiskserver"])
            except:
                pass
            try:
                run(["docker", "volume", "rm", "memorydiskserver"])
            except:
                pass
            try:
                dvol(["rm", "-f", "memorydiskserver"])
            except:
                pass
        cleanup()
        self.addCleanup(cleanup)

    def start_memorydiskserver(self):
        """
        Standard start for memorydiskserver.
        """
        run([
            "docker", "run", "--name", "memorydiskserver", "-d",
            "-v", "memorydiskserver:/data", "--volume-driver", "dvol",
            "-p", "8080:80", "clusterhq/memorydiskserver",
        ])

    def test_docker_run_test_container(self):
        def cleanup():
            run(["docker", "rm", "-f", "memorydiskserver"])
        try:
            cleanup()
        except:
            pass
        run([
            "docker", "run", "--name", "memorydiskserver", "-d",
            "-p", "8080:80", "clusterhq/memorydiskserver"
        ])

        wait_for_server = try_until(
            lambda: get("http://" + docker_host() + ":8080/get")
        )
        self.assertEqual(wait_for_server.content, "Value: ")

    def test_docker_run_dvol_creates_volumes(self):
        self.cleanup_memorydiskserver()
        self.start_memorydiskserver()

        def dvol_list_includes_memorydiskserver():
            result = dvol(["list"])
            if "memorydiskserver" not in result:
                raise Exception("volume never showed up in result %s" % (result,))
        try_until(dvol_list_includes_memorydiskserver)

    def test_docker_run_dvol_container_show_up_in_list_output(self):
        container = "fancy"
        def cleanup():
            cmds = [
                ["docker", "rm", "-f", container],
                ["docker", "volume", "rm", "memorydiskserver"],
                [DVOL, "rm", "-f", "memorydiskserver"],
            ]
            for cmd in cmds:
                try:
                    run(cmd)
                except:
                    pass
        cleanup()
        self.addCleanup(cleanup)
        run([
            "docker", "run", "--name", container, "-d",
            "-v", "memorydiskserver:/data", "--volume-driver", "dvol",
            "clusterhq/memorydiskserver"
        ])
        def dvol_list_includes_container_name():
            result = dvol(["list"])
            if "/" + container not in result:
                raise Exception("container never showed up in result %s" % (result,))
        try_until(dvol_list_includes_container_name)

    def test_docker_run_dvol_multiple_containers_shows_up_in_list_output(self):
        container1 = "fancy"
        container2 = "fancier"
        def cleanup():
            cmds = [
                ["docker", "rm", "-f", container1],
                ["docker", "rm", "-f", container2],
                ["docker", "volume", "rm", "memorydiskserver"],
                [DVOL, "rm", "-f", "memorydiskserver"],
            ]
            for cmd in cmds:
                try:
                    run(cmd)
                except:
                    pass
        cleanup()
        self.addCleanup(cleanup)
        run([
            "docker", "run", "--name", container1, "-d",
            "-v", "memorydiskserver:/data", "--volume-driver", "dvol",
            "clusterhq/memorydiskserver"
        ])
        run([
            "docker", "run", "--name", container2, "-d",
            "-v", "memorydiskserver:/data", "--volume-driver", "dvol",
            "clusterhq/memorydiskserver"
        ])
        def dvol_list_includes_container_names():
            result = dvol(["list"])
            # Either way round is OK
            if (("/" + container1 + ",/" + container2 not in result) and
                ("/" + container2 + ",/" + container1 not in result)):
                raise Exception(
                        "containers never showed up in result %s" % (result,)
                )
        try_until(dvol_list_includes_container_names)

    def test_docker_run_roundtrip_value(self):
        self.cleanup_memorydiskserver()
        self.start_memorydiskserver()

        for value in ("10", "20"):
            # Running test with multiple values forces container to persist it
            # in memory (rather than hard-coding the response to make the test
            # pass).
            try_until(
                lambda: get(
                    "http://" + docker_host() + ":8080/set?value=%s" % (value,)
                )
            )
            getting_value = try_until(
                lambda: get("http://" + docker_host() + ":8080/get")
            )
            self.assertEqual(getting_value.content, "Value: %s" % (value,))

    def try_set_memorydiskserver_value(self, value):
        """
        Set a memorydiskserver value and wait for it to complete.
        """
        try_until(lambda: get(
            "http://%s:8080/set?value=%s" % (docker_host(), value,)
        ))

    def try_get_memorydiskserver_value(self):
        """
        Get a memorydiskserver value and wait for it to return.
        """
        return try_until(lambda: get(
            "http://%s:8080/get" % (docker_host(),)
        )).content

    @skip_if_go_version
    def test_switch_branches_restarts_containers(self):
        """
        Docker containers are restarted when switching branches.
        """
        self.cleanup_memorydiskserver()
        self.start_memorydiskserver()

        # We have to do an initial state commit before we can switch branches
        dvol(["commit", "-m", "Initial"])

        dvol(["checkout", "-b", "alpha"])
        self.try_set_memorydiskserver_value("alpha")
        dvol(["commit", "-m", "alpha"])

        dvol(["checkout", "-b", "beta"])
        self.try_set_memorydiskserver_value("beta")
        dvol(["commit", "-m", "beta"])

        current_value = self.try_get_memorydiskserver_value()
        self.assertEqual(current_value, "Value: beta")

        dvol(["checkout", "alpha"])
        current_value = self.try_get_memorydiskserver_value()
        self.assertEqual(current_value, "Value: alpha")

    @skip_if_python_version # The Python implementation is broken
    def test_docker_volumes_removed(self):
        """
        When a dvol volume is removed, you can implicitly create a new volume
        using `docker run` and it succeeds.
        """
        def cleanup():
            try:
                run(["docker", "rm", "-fv", "volume_remove_test"])
            except:
                pass
            try:
                run(["docker", "rm", "-fv", "volume_remove_test_error"])
            except:
                pass
            try:
                run(["docker", "volume", "rm", "volume-remove-test"])
                pass
            except:
                pass
            try:
                dvol(["rm", "-f", "volume-remove-test"])
                pass
            except:
                pass
        cleanup()
        self.addCleanup(cleanup)

        # Start a new container
        run(["docker", "run", "--name", "volume_remove_test", "-v",
            "volume-remove-test:/data", "--volume-driver", "dvol", "-d",
            "busybox", "true"])

        # Remove the volume
        dvol(["rm", "-f", "volume-remove-test"])

        # Start a new container on the same volume and there are no errors
        run(["docker", "run", "--name", "volume_remove_test_error", "-v",
            "volume-remove-test:/data", "--volume-driver", "dvol", "-d",
            "busybox", "true"])

    @skip_if_python_version
    @skip_if_docker_version_less_than("1.10.0")
    def test_dvol_volumes_listed_in_docker(self):
        """
        Volumes created with dvol an be listed in `docker volume ls`.
        """
        def cleanup():
            try:
                run(["docker", "volume", "rm", "docker-volume-list-test"])
            except:
                pass
            try:
                dvol(["rm", "-f", "docker-volume-list-test"])
            except:
                pass

        cleanup()
        self.addCleanup(cleanup)

        dvol(["init", "docker-volume-list-test"])

        docker_output = run(["docker", "volume", "ls"])

        for line in docker_output.split("\n"):
            if line.startswith("dvol") and "docker-volume-list-test" in line:
                return

        self.fail("Volume 'docker-volume-list-test' not found in Docker "
                "output:\n\n" + docker_output)

    def test_implicit_creation(self):
        """
        ``docker run`` with the dvol volume driver creates a master branch.
        """
        volume_name = 'docker-volume-implicit-creation-test'
        volume_directory = "/data"
        docker_volume_arg = '%s:/%s' % (volume_name, volume_directory)

        # XXX: This is a) duplicated, b) dangerous, as the bare `except` masks
        # real errors.
        def cleanup():
            try:
                run(["docker", "volume", "rm", volume_name])
            except:
                pass
            try:
                dvol(["rm", "-f", volume_name])
            except:
                pass
        cleanup()
        self.addCleanup(cleanup)

        run(['docker', 'run', '--rm', '-v', docker_volume_arg,
             '--volume-driver=dvol', 'busybox',
             'sh', '-c', 'echo word > /%s/file' % (volume_directory,)])

        branch_output = dvol(["branch"])
        self.assertIn('* master', branch_output)

    def test_unique_volumes(self):
        """
        Two separate volumes do not share the same filesystem namespace.
        """
        alpha = "test-unique-volume-alpha"
        beta = "test-unique-volume-beta"
        def cleanup():
            for volume in [alpha, beta]:
                try: run(["docker", "rm", "-fv", volume])
                except: pass
                try: run(["docker", "volume", "rm", volume])
                except: pass
                try: dvol(["rm", "-f", volume])
                except: pass
        cleanup()
        self.addCleanup(cleanup)

        for volume in [alpha, beta]:
            run(["docker", "run", "-v", "%s:/data" % (volume,),
                "--volume-driver", "dvol", "--name", volume, "ubuntu", "bash",
                "-c", "echo -n %s > /data/data" % (volume,)])
            run(["docker", "rm", volume]) # using volume as the container name

        data = dict()
        for volume in [alpha, beta]:
            result = run(["docker", "run", "-v", "%s:/data" % (volume,),
                "--volume-driver", "dvol", "--name", volume, "ubuntu",
                "cat", "/data/data"])
            data[volume] = result

        # These could be moved into the loop above, but leave them here so it
        # is clearer which is failing.
        self.assertEqual(data[alpha], alpha)
        self.assertEqual(data[beta], beta)

    def _get_me_a_server(self, volume):
        # XXX: This will block forever, which means we can't use the tests.
        s = socket.socket()
        s.bind(('', 0))
        port = 8080 # s.getsockname()[1]
        s.close()
        stdout = open("test_plugin.stdout.txt", "w+t")
        stderr = open("test_plugin.stderr.txt", "w+t")
        process = async_docker([
            "run", "--rm", "-i",
            "-v", "/var/lib/dvol:/var/lib/dvol",
            "-v", "/run/docker/plugins:/run/docker/plugins",
            "-v", "/var/run/docker.sock:/var/run/docker.sock",
            "-v", "{}:/pwd".format(os.getcwd()),
            "-p", "8080:{}".format(port),
            "clusterhq/dvol:golang", "dvol",
            "serve", volume,
            ], stdout, stderr)
        self.addCleanup(process.terminate)

        # XXX: Get this from the output of `dvol serve`
        base_href = b'http://{}:{}/'.format(docker_host(), port)
        try:
            try_until(lambda: get(base_href))
        except:
            stdout.seek(0)
            stderr.seek(0)
            print("Some problem, we had a thing: {}, {}".format(
                stdout.read(),
                stderr.read(),
            ))
            raise
        return base_href

    def _push_and_pull(self, volume_name, container_path, message):
        docker_volume_arg = '%(volume_name)s:/%(container_path)s' % dict(
            volume_name=volume_name, container_path=container_path)

        def cleanup():
            try:
                run(["docker", "volume", "rm", volume_name])
            except:
                pass
            try:
                dvol(["rm", "-f", volume_name])
            except:
                pass
        cleanup()
        self.addCleanup(cleanup)

        dvol(['init', volume_name])

        # XXX: we don't want to use `volume_name` here, we instead want the
        # path to the volume.
        server = self._get_me_a_server(volume_name)

        run(['docker', 'run', '--rm', '-v', docker_volume_arg,
            '--volume-driver=dvol',
            'busybox', 'sh', '-c', 'echo word > /%s/file' % (container_path,)])
        dvol(['commit', '-m', message])
        # Implicitly uses volume_name volume because it was created most
        # recently.
        dvol(['push', server])
        dvol(['rm', '-f', volume_name])
        dvol(['clone', server, volume_name])

    @skip_if_python_version  # Not implemented for Python.
    def test_roundtrip_dvol_to_itself(self):
        """
        * Assume unauthenticated pushes
        """
        volume_name = 'foo' # _{}_{}'.format(os.getpid(), os.randrange(10000))
        container_path = 'bar'
        self._push_and_pull(volume_name, container_path, "Hello world.")
        # XXX Duplication with _push_and_pull
        docker_volume_arg = '%(volume_name)s:/%(container_path)s' % dict(
            volume_name=volume_name, container_path=container_path)
        output = run(["docker", "run", "--rm", "-v", docker_volume_arg,
            "--volume-driver=dvol", "busybox",
            "cat", "/%s/file" % (container_path,)])
        self.assertEqual(output, "word")

    @skip_if_python_version
    def test_roundtrip_dvol_metadata_to_itself(self):
        """
        ``dvol clone`` produces a repository containing the same metadata as
        the repository being cloned.
        """
        volume_name = 'foo'
        container_path = 'bar'
        commit_message = 'Here is a commit message'
        self._push_and_pull(volume_name, container_path, commit_message)
        result = dvol(["--output-format=json", "log"])
        self.assertEqual(
            [{"message": commit_message}],
            parse_json(result),
        )

def parse_json(s):
    try:
        return json.loads(s)
    except (TypeError, ValueError) as e:
        raise ValueError('Could not decode JSON: {} ({})'.format(s, e))

"""
log of integration tests to write:

write test_switch_branches_restarts_containers

command:
    dvol commit ...
expected behaviour:
    a container which only persists its in-memory state to disk occasionally (e.g. on shutdown) has correctly written out its state

command:
    dvol reset...
expected behaviour:
    a container which caches disk state in memory has correctly updated its state (IOW, containers get restarted around rollbacks)

destroying a dvol volume also destroys any containers using that volume, and destroys the docker volume reference to that dvol volume (without ``docker volume`` subcommand, this can be tested by attempting to start a new container using that volume)
"""
