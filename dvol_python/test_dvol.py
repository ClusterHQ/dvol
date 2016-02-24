"""
Tests for the Voluminous CLI.
"""

from string import letters

from hypothesis import given
from hypothesis.strategies import binary, characters, dictionaries, sets, text

from twisted.trial.unittest import TestCase
from twisted.python.filepath import FilePath
from dvol import VolumeAlreadyExists
from twisted.python.usage import UsageError
import subprocess
import os

TEST_DVOL_BINARY = os.environ.get("TEST_DVOL_BINARY", False)
DVOL_BINARY = os.environ.get("DVOL_BINARY", "./dvol")
ARGS = ["--disable-docker-integration"]


class CalledProcessErrorWithOutput(Exception):
    pass

if TEST_DVOL_BINARY:
    # Test an alternative implementation of dvol, such as one available as a
    # binary rather than an importable Python implementation.
    class FakeVoluminous(object):
        def __init__(self):
            self._output = []

        def getOutput(self):
            """
            Return a list of process outputs
            """
            return self._output

        def report_output(self, output):
            self._output.append(output)

    class VoluminousOptions(object):
        def __init__(self):
            self.voluminous = FakeVoluminous()

        def parseOptions(self, args):
            try:
                cmd = [DVOL_BINARY] + args
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
            result = result[:-1]
            self.voluminous.report_output(result)

else:
    from dvol import VoluminousOptions


def items(d):
    """
    Return the tuples that make up a dictionary.

    :param Map[a, b] d: A dictionary.
    :rtype: [(a, b)]
    """
    return list(d.items())


def path_segments():
    """
    Strategy for generating path segments that we support.
    """
    # XXX: Fix the bug about empty volume names
    # XXX: Handle unicode / weird volume names by rejecting them in dvol
    # XXX: Impose a maximum volume name length (at least so rendering is easy!)
    # XXX: How do we handle case-insensitive file systems?
    # XXX: Fix more boring wrapping output bugs (112 was too large, here).
    return text(
        alphabet=letters, min_size=1, max_size=40).map(lambda t: t.lower())


volume_names = path_segments
branch_names = path_segments


class VoluminousTests(TestCase):
    def setUp(self):
        self.tmpdir = FilePath(self.mktemp())
        self.tmpdir.makedirs()

    def test_create_volume(self):
        # TODO test volume names with '/' in them - they should not end up
        # making nested heirarchy
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
        self.assertTrue(self.tmpdir.child("foo").exists())
        self.assertTrue(self.tmpdir.child("foo").child("branches")
                .child("master").exists())
        self.assertEqual(dvol.voluminous.getOutput(),
                ["Created volume foo\nCreated branch foo/master"])

    def test_create_volume_already_exists(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
        expected_output = "Error: volume foo already exists"
        try:
            dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
            # TODO assert exit code != 0
            self.assertTrue(dvol.voluminous.getOutput()[-1].strip().endswith(
                    expected_output))
        except VolumeAlreadyExists:
            # in non-out-of-process case, we'll get this exception. This is OK.
            pass
        except CalledProcessErrorWithOutput, error:
            self.assertTrue(error.original.output, expected_output)
            self.assertTrue(error.original.returncode != 0)

    def test_commit_no_message_raises_error(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
        try:
            dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "commit"])
            # TODO assert exit code != 0
            self.assertTrue(dvol.voluminous.getOutput()[-1].strip().endswith(
                    "You must provide a commit message"))
        except UsageError:
            # in non-out-of-process case, we'll get this exception. This is OK.
            pass
    if TEST_DVOL_BINARY:
        test_commit_no_message_raises_error.todo = "not expected to work in go version"

    def test_commit_volume(self):
        # TODO need to assert that containers using this volume get stopped
        # and started around commits
        # TODO test snapshotting nonexistent volume
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
        volume = self.tmpdir.child("foo")
        volume.child("branches").child("master").child(
            "file.txt").setContent("hello!")
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "commit", "-m", "hello from 30,000 ft"])
        commitId = dvol.voluminous.getOutput()[-1]
        commit = volume.child("commits").child(commitId)
        self.assertTrue(commit.exists())
        self.assertTrue(commit.child("file.txt").exists())
        self.assertEqual(commit.child("file.txt").getContent(), "hello!")
    if TEST_DVOL_BINARY:
        test_commit_volume.todo = "not expected to work in go version"

    def test_list_empty_volumes(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "list"])
        self.assertEqual(dvol.voluminous.getOutput(), ["  VOLUME   BRANCH   CONTAINERS "])
    if TEST_DVOL_BINARY:
        test_list_empty_volumes.todo = "not expected to work in go version"

    @given(volumes=sets(volume_names(), min_size=1, average_size=10).map(list))
    def test_list_multi_volumes(self, volumes):
        tmpdir = FilePath(self.mktemp())
        tmpdir.makedirs()

        dvol = VoluminousOptions()
        for name in volumes:
            dvol.parseOptions(ARGS + ["-p", tmpdir.path, "init", name])
        dvol.parseOptions(ARGS + ["-p", tmpdir.path, "list"])

        lines = dvol.voluminous.getOutput()[-1].split("\n")
        header, rest = lines[0], lines[1:]
        expected_volumes = [[name, 'master'] for name in volumes]
        # `init` activates the volume, so the last initialized volume is the
        # active one.
        expected_volumes[-1] = ['*', expected_volumes[-1][0], expected_volumes[-1][1]]
        self.assertEqual(['VOLUME', 'BRANCH', 'CONTAINERS'], header.split())
        self.assertEqual(
            sorted(expected_volumes),
            sorted([line.split() for line in rest]),
        )
    if TEST_DVOL_BINARY:
        test_list_multi_volumes.todo = "not expected to work in go version"

    @given(volumes=dictionaries(
        volume_names(), branch_names(), min_size=1).map(items))
    def test_branch_multi_volumes(self, volumes):
        """
        Always show the last checked-out branch for all volumes in ``list``.
        """
        tmpdir = FilePath(self.mktemp())
        tmpdir.makedirs()

        dvol = VoluminousOptions()
        for volume, branch in volumes:
            dvol.parseOptions(ARGS + ["-p", tmpdir.path, "init", volume])
            dvol.parseOptions(ARGS + ["-p", tmpdir.path, "commit", "-m", "hello"])
            dvol.parseOptions(ARGS + ["-p", tmpdir.path, "checkout", "-b", branch])

        dvol.parseOptions(ARGS + ["-p", tmpdir.path, "list"])
        lines = dvol.voluminous.getOutput()[-1].split("\n")
        header, rest = lines[0], lines[1:]

        expected_volumes = [[volume, branch] for volume, branch in volumes]
        # `init` activates the volume, so the last initialized volume is the
        # active one.
        expected_volumes[-1] = [
            '*', expected_volumes[-1][0], expected_volumes[-1][1]]
        self.assertEqual(['VOLUME', 'BRANCH', 'CONTAINERS'], header.split())
        self.assertEqual(
            sorted(expected_volumes),
            sorted([line.split() for line in rest]),
        )
    if TEST_DVOL_BINARY:
        test_branch_multi_volumes.todo = "not expected to work in go version"

    @given(volume_name=volume_names(), branch_name=branch_names(),
           commit_message=text(characters(min_codepoint=1, max_codepoint=127), min_size=1),
           filename=path_segments(), content=binary())
    def test_non_standard_branch(self, volume_name, branch_name, commit_message, filename,
                                 content):
        tmpdir = FilePath(self.mktemp())
        tmpdir.makedirs()

        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ['-p', tmpdir.path, 'init', volume_name])
        volume = tmpdir.child(volume_name)
        volume.child("branches").child("master").child(filename).setContent(content)
        dvol.parseOptions(ARGS + ["-p", tmpdir.path, "commit", "-m", commit_message])
        dvol.parseOptions(ARGS + ["-p", tmpdir.path, "checkout", "-b", branch_name])
        dvol.parseOptions(ARGS + ["-p", tmpdir.path, "list"])
        lines = dvol.voluminous.getOutput()[-1].split("\n")
        header, rest = lines[0], lines[1:]
        self.assertEqual(['VOLUME', 'BRANCH', 'CONTAINERS'], header.split())
        self.assertEqual(
            [['*', volume_name, branch_name]], [line.split() for line in rest])
    if TEST_DVOL_BINARY:
        test_non_standard_branch.todo = "not expected to work in go version"

    def test_log(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "init", "foo"])
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "commit", "-m", "oi"])
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "commit", "-m", "you"])
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "log"])
        actual = dvol.voluminous.getOutput()[-1]
        expected = (
            "commit\n"
            "Author:\n"
            "Date:\n"
            "\n"
            "    you\n"
            "\n"
            "commit\n"
            "Author:\n"
            "Date:\n"
            "\n"
            "    oi\n")
        expectedLines = expected.split("\n")
        actualLines = actual.split("\n")
        self.assertEqual(len(expectedLines), len(actualLines))
        for expected, actual in zip(
                expectedLines, actualLines):
            self.assertTrue(actual.startswith(expected))
    if TEST_DVOL_BINARY:
        test_log.todo = "not expected to work in go version"

    def test_reset(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
        volume = self.tmpdir.child("foo")
        volume.child("branches").child("master").child(
            "file.txt").setContent("alpha")
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "commit", "-m", "commit 1"])
        commitId = dvol.voluminous.getOutput()[-1]
        commit = volume.child("commits").child(commitId)
        self.assertTrue(commit.exists())
        self.assertTrue(commit.child("file.txt").exists())
        self.assertEqual(commit.child("file.txt").getContent(), "alpha")
        volume.child("branches").child("master").child(
            "file.txt").setContent("beta")
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "reset", "--hard", commitId])
        self.assertEqual(volume.child("branches").child("master")
                .child("file.txt").getContent(), "alpha")
    if TEST_DVOL_BINARY:
        test_reset.todo = "not expected to work in go version"

    def test_reset_HEAD(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
        volume = self.tmpdir.child("foo")
        volume.child("branches").child("master").child(
            "file.txt").setContent("alpha")
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "commit", "-m", "commit 1"])
        volume.child("branches").child("master").child(
            "file.txt").setContent("beta")
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "reset", "--hard", "HEAD"])
        # working copy is changed
        self.assertEqual(volume.child("branches").child("master")
                .child("file.txt").getContent(), "alpha")
    if TEST_DVOL_BINARY:
        test_reset_HEAD.todo = "not expected to work in go version"

    def test_reset_HEAD_multiple_commits(self):
        # assert that the correct (latest) commit is rolled back to
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
        volume = self.tmpdir.child("foo")

        volume.child("branches").child("master").child(
            "file.txt").setContent("BAD")
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "commit", "-m", "commit 1"])

        volume.child("branches").child("master").child(
            "file.txt").setContent("alpha")
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "commit", "-m", "commit 2"])

        volume.child("branches").child("master").child(
            "file.txt").setContent("beta")
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "reset", "--hard", "HEAD"])
        # working copy is changed from beta to alpha, but not BAD
        self.assertEqual(volume.child("branches").child("master")
                .child("file.txt").getContent(), "alpha")
    if TEST_DVOL_BINARY:
        test_reset_HEAD_multiple_commits.todo = "not expected to work in go version"

    def test_reset_HEAD_hat_multiple_commits(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
        volume = self.tmpdir.child("foo")

        volume.child("branches").child("master").child(
            "file.txt").setContent("OLD")
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "commit", "-m", "commit 1"])
        oldCommit = dvol.voluminous.getOutput()[-1]

        volume.child("branches").child("master").child(
            "file.txt").setContent("NEW")
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "commit", "-m", "commit 2"])
        newCommit = dvol.voluminous.getOutput()[-1]

        volume.child("branches").child("master").child(
            "file.txt").setContent("NEWER")

        # both exist
        self.assertTrue(volume.child("commits").child(oldCommit).exists())
        self.assertTrue(volume.child("commits").child(newCommit).exists())

        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "reset", "--hard", "HEAD^"])
        self.assertEqual(volume.child("branches").child("master")
                .child("file.txt").getContent(), "OLD")

        # newest commit has been wiped out
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "log"])
        actual = dvol.voluminous.getOutput()[-1]
        self.assertEqual(len(actual.split("\n")), 6) # 6 lines = 1 commit

        # only old exists
        self.assertTrue(volume.child("commits").child(oldCommit).exists())
        self.assertFalse(volume.child("commits").child(newCommit).exists())
    if TEST_DVOL_BINARY:
        test_reset_HEAD_hat_multiple_commits.todo = "not expected to work in go version"

    def test_branch_default_master(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "branch"])
        actual = dvol.voluminous.getOutput()[-1]
        self.assertEqual(actual.strip(), "* master")
    if TEST_DVOL_BINARY:
        test_branch_default_master.todo = "not expected to work in go version"

    def test_create_branch_from_current_HEAD(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])

        volume = self.tmpdir.child("foo")
        volume.child("branches").child("master").child(
            "file.txt").setContent("hello")
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "commit", "-m", "commit 1"])

        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "checkout", "-b", "newbranch"])
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "branch"])
        actual = dvol.voluminous.getOutput()[-1]
        self.assertEqual(actual, "  master\n* newbranch")

        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "log"])
        actual = dvol.voluminous.getOutput()[-1]
        # the commit should have been "copied" to the new branch
        self.assertEqual(len(actual.split("\n")), 6) # 6 lines = 1 commit
    if TEST_DVOL_BINARY:
        test_create_branch_from_current_HEAD.todo = "not expected to work in go version"

    def test_rollback_branch_doesnt_delete_referenced_data_in_other_branches(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
        volume = self.tmpdir.child("foo")

        volume.child("branches").child("master").child(
            "file.txt").setContent("OLD")
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "commit", "-m", "commit 1"])
        oldCommit = dvol.voluminous.getOutput()[-1]

        volume.child("branches").child("master").child(
            "file.txt").setContent("NEW")
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "commit", "-m", "commit 2"])
        newCommit = dvol.voluminous.getOutput()[-1]

        volume.child("branches").child("master").child(
            "file.txt").setContent("NEWER")

        # both exist
        self.assertTrue(volume.child("commits").child(oldCommit).exists())
        self.assertTrue(volume.child("commits").child(newCommit).exists())

        # create new branch from current HEAD, and then switch back to master.
        # should protect commit *data* from being destroyed when we later
        # rollback.
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "checkout", "-b", "newbranch"])
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "checkout", "master"])

        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "reset", "--hard", "HEAD^"])
        self.assertEqual(volume.child("branches").child("master")
                .child("file.txt").getContent(), "OLD")

        # newest commit has been wiped out in master branch metadata
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "log"])
        actual = dvol.voluminous.getOutput()[-1]
        self.assertEqual(len(actual.split("\n")), 6) # 6 lines = 1 commit

        # new still exists because it's referenced in another branch
        self.assertTrue(volume.child("commits").child(oldCommit).exists())
        self.assertTrue(volume.child("commits").child(newCommit).exists())
    if TEST_DVOL_BINARY:
        test_rollback_branch_doesnt_delete_referenced_data_in_other_branches.todo = "not expected to work in go version"
