"""
Tests for dvol docker integration.

Assumes we:
* have docker running and are running as root or a user in the docker group
* have dvol under test installed in /usr/local/bin (as per Makefile)
* have dvol docker plugin installed and running
* are not running in parallel with ourselves
* have access to ports on the machine
"""

from twisted.trial.unittest import TestCase
from twisted.python.filepath import FilePath
import subprocess
import requests
import time
from os import environ

def docker_host():
    return environ.get("DOCKER_HOST").split("://")[1].split(":")[0]

def retry(f, attempts=5, backoff=0.1, attempt=1):
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
        return retry(
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
        try:
            run(["docker", "rm", "-f", "memorydiskserver"])
        except:
            pass
        run([
            "docker","run", "--name", "memorydiskserver", "-d",
            "-p", "8080:80", "clusterhq/memorydiskserver"
        ])
        wait_for_server = retry(
            lambda: requests.get("http://" + docker_host() + ":8080/get")
        )
        self.assertEqual(wait_for_server.content, "Hi there, I love get!")
        run(["docker", "rm", "-f", "memorydiskserver"])


"""
log of integration tests to write:

write test_switch_branches_restarts_containers

command:
    docker-compose up -d (in a directory with appropriate docker-compose.yml file)
expected behaviour:
    docker containers are started with dvol accordingly

command:
    docker run -ti --volume-driver dvol -v hello:/data busybox sh
expected output:
    dvol volume is created on-demand

command:
    dvol commit ...
expected behaviour:
    a container which only persists its in-memory state to disk occasionally (e.g. on shutdown) has correctly written out its state

command:
    dvol reset...
expected behaviour:
    a container which caches disk state in memory has correctly updated its state (IOW, containers get restarted around rollbacks)

command:
    run a container using a dvol volume
expected behaviour:
    dvol list
    container names shows up in output
"""
