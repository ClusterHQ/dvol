"""
Common test tools.
"""

from os import environ
from semver import compare
from unittest import skipIf
import requests
import subprocess
import time

TEST_GOLANG_VERSION = environ.get("TEST_GOLANG_VERSION", False)
DOCKER_VERSION = environ.get("DOCKER_VERSION", "")

skip_if_go_version = skipIf(
    TEST_GOLANG_VERSION,
    "Not expected to work in go version"
)

skip_if_python_version = skipIf(
    not TEST_GOLANG_VERSION,
    "Not expected to work in Python version"
)

def _skip_max_docker_ver(ver):
    try:
        return compare(DOCKER_VERSION, ver) < 0
    except ValueError:
        return False

skip_if_docker_version_less_than = lambda ver: skipIf(
    _skip_max_docker_ver(ver),
    "Not expected to work in this Docker version")


def get(*args, **kw):
    response = requests.get(*args, **kw)
    if response.status_code != 200:
        raise Exception("Not 200: %s" % (response,))
    return response

def docker_host():
    if "DOCKER_HOST" not in environ:
        return "localhost"
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
