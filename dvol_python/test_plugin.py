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

from twisted.trial.unittest import TestCase
from twisted.python.filepath import FilePath
import subprocess
import requests
import time
from os import environ

DVOL = "/usr/local/bin/dvol"

def get(*args, **kw):
    response = requests.get(*args, **kw)
    if response.status_code != 200:
        raise Exception("Not 200: %s" % (response,))
    return response

def docker_host():
    return environ.get("DOCKER_HOST").split("://")[1].split(":")[0]

def try_until(f, attempts=5, backoff=0.1, attempt=1):
    """
    Synchronously, retry ``f`` every ``backoff`` * (2 ^ ``attempt``) seconds
    until it doesn't raise an exception, or we've tried ``attempts`` many
    times. Return the result of running ``f`` successfully, or raise the last
    exception it raised when attempted.
    """
    try:
        return f()
    except:
        if attempt > attempts:
            raise
        time.sleep(backoff * (2 ** attempt))
        return try_until(
                f, attempts=attempts, backoff=backoff, attempt=attempt + 1)


class CalledProcessErrorWithOutput(Exception):
    pass

def run(cmd):
    """
    Run cmd (list of bytes), e.g. ["ls", "/"] and return the result, raising
    CalledProcessErrorWithOutput if return code is non-zero.
    """
    try:
        result = subprocess.check_output(
            cmd,
            stderr=subprocess.STDOUT
        )
    except subprocess.CalledProcessError, error:
        exc = CalledProcessErrorWithOutput(
            "\n>> command:\n%(command)s"
            "\n>> returncode\n%(returncode)d"
            "\n>> output:\n%(output)s" %
            dict(command=" ".join(cmd),
                 returncode=error.returncode,
                 output=error.output))
        exc.original = error
        raise exc
    return result

class VoluminousTests(TestCase):
    def setUp(self):
        self.tmpdir = FilePath(self.mktemp())
        self.tmpdir.makedirs()

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
        cleanup()

    def test_docker_run_dvol_creates_volumes(self):
        def cleanup():
            run(["docker", "rm", "-f", "memorydiskserver"])
            run([DVOL, "rm", "-f", "memorydiskserver"])
        try:
            cleanup()
        except:
            pass
        run([
            "docker", "run", "--name", "memorydiskserver", "-d",
            "-v", "memorydiskserver:/data", "--volume-driver", "dvol",
            "clusterhq/memorydiskserver"
        ])
        def dvol_list_includes_memorydiskserver():
            result = run([DVOL, "list"])
            if "memorydiskserver" not in result:
                raise Exception("volume never showed up in result %s" % (result,))
        try_until(dvol_list_includes_memorydiskserver)
        cleanup()

    def test_docker_run_dvol_container_show_up_in_list_output(self):
        container = "fancy"
        def cleanup():
            run(["docker", "rm", "-f", container])
            run([DVOL, "rm", "-f", "memorydiskserver"])
        try:
            cleanup()
        except:
            pass
        run([
            "docker", "run", "--name", container, "-d",
            "-v", "memorydiskserver:/data", "--volume-driver", "dvol",
            "clusterhq/memorydiskserver"
        ])
        def dvol_list_includes_container_name():
            result = run([DVOL, "list"])
            if "/" + container not in result:
                raise Exception("container never showed up in result %s" % (result,))
        try_until(dvol_list_includes_container_name)
        cleanup()

    def test_docker_run_dvol_multiple_containers_shows_up_in_list_output(self):
        container1 = "fancy"
        container2 = "fancier"
        def cleanup():
            run(["docker", "rm", "-f", container1])
            run(["docker", "rm", "-f", container2])
            run([DVOL, "rm", "-f", "memorydiskserver"])
        try:
            cleanup()
        except:
            pass
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
            result = run([DVOL, "list"])
            # Either way round is OK
            if (("/" + container1 + ",/" + container2 not in result) and
                ("/" + container2 + ",/" + container1 not in result)):
                raise Exception(
                        "containers never showed up in result %s" % (result,)
                )
        try_until(dvol_list_includes_container_names)
        cleanup()

    def test_docker_run_roundtrip_value(self):
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
        cleanup()
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
