"""
Tests for the dvol CLI.
"""

from string import letters

from hypothesis import given
from hypothesis.strategies import binary, characters, dictionaries, sets, text

from twisted.trial.unittest import TestCase
from twisted.python.filepath import FilePath
from twisted.python.usage import UsageError
import subprocess
import os
import json

from testtools import (
    CalledProcessErrorWithOutput, TEST_GOLANG_VERSION, skip_if_python_version
)

DVOL_BINARY = os.environ.get("DVOL_BINARY", "./dvol")
ARGS = ["--disable-docker-integration"]

if TEST_GOLANG_VERSION:
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
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
        self.assertTrue(self.tmpdir.child("foo").exists())
        self.assertTrue(self.tmpdir.child("foo").child("branches")
                .child("master").exists())
        self.assertEqual(dvol.voluminous.getOutput()[-1],
                "Created volume foo\nCreated branch foo/master")
        # Verify operation with `list`
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "list"])
        header, rest = self._parse_list_output(dvol)
        expected_volumes = [["*", "foo", "master"]]
        self.assertEqual(
            sorted(expected_volumes),
            sorted(rest),
        )

    def test_create_volume_already_exists(self):
        dvol = VoluminousOptions()
        # Create the repository twice, second time should have the error
        expected_output = "Error: volume foo already exists"
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
        try:
            dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
            self.assertEqual(dvol.voluminous.getOutput()[-1], expected_output)
        except CalledProcessErrorWithOutput, error:
            self.assertIn(expected_output, error.original.output)
            self.assertTrue(error.original.returncode != 0)

    def test_create_volume_with_path_separator(self):
        dvol = VoluminousOptions()
        try:
            dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo/bar"])
            output = dvol.voluminous.getOutput()[-1]
        except CalledProcessErrorWithOutput, error:
            output = error.original.output
        self.assertIn("Error", output)
        self.assertIn("foo/bar", output)

    def _parse_list_output(self, dvol):
        """
        Return a tuple containing the first line of output, and then the
        remaining lines of output from the last command output in the dvol
        object.
        """
        lines = dvol.voluminous.getOutput()[-1].split("\n")
        return lines[0].split(), [line.split() for line in lines[1:]]

    def test_switch_active_volume(self):
        """
        ``dvol switch`` should switch the currently active volume
        stored in the current_volume.json file.

        Assert whiteboxy things about the implementation, because
        we care about upgradeability (wrt on-disk format) between
        different implementations.
        """
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "bar"])
        self.assertEqual(
            json.loads(self.tmpdir.child("current_volume.json").getContent()),
            dict(current_volume="bar")
        )
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "switch", "foo"])
        self.assertEqual(
            json.loads(self.tmpdir.child("current_volume.json").getContent()),
            dict(current_volume="foo")
        )
        # Verify operation with `list`
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "list"])
        header, rest = self._parse_list_output(dvol)
        expected_volumes = [["*", "foo", "master"], ["bar", "master"]]
        self.assertEqual(
            sorted(expected_volumes),
            sorted(rest),
        )

    @skip_if_python_version
    def test_switch_volume_does_not_exist(self):
        """
        ``dvol switch`` should give a meaningful error message if the
        volume we try to switch to doesn't exist.
        """
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
        try:
            dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "switch", "bar"])
        except CalledProcessErrorWithOutput, error:
            self.assertEqual(error.original.output.rstrip(), "Error: bar does not exist")

    def test_created_volume_active_after_switch(self):
        """
        After we have used ``dvol switch`` to switch volume, ``dvol init``
        should be able to set the active volume to the one just created.
        """
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "bar"])
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "switch", "foo"])
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "baz"])
        self.assertEqual(
            json.loads(self.tmpdir.child("current_volume.json").getContent()),
            dict(current_volume="baz")
        )
        # Verify operation with `list`
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "list"])
        header, rest = self._parse_list_output(dvol)
        expected_volumes = [
            ["foo", "master"], ["bar", "master"], ["*", "baz", "master"]
        ]
        self.assertEqual(
            sorted(expected_volumes),
            sorted(rest),
        )

    def test_commit_no_message_raises_error(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
        # TODO after throwing away python version, make this test stricter
        # about exit code != 0
        try:
            try:
                dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "commit"])
            except CalledProcessErrorWithOutput, error: # go version
                expected_output = "You must provide a commit message"
                self.assertIn(expected_output, error.original.output)
                self.assertTrue(error.original.returncode != 0)
        except UsageError: # python version
            # in non-out-of-process case, we'll get this exception. This is OK.
            pass

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

    def test_list_empty_volumes(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "list"])
        self.assertIn(
            dvol.voluminous.getOutput()[-1].strip(),
            "  VOLUME   BRANCH   CONTAINERS"
        )

    @given(volumes=sets(volume_names(), min_size=1, average_size=10).map(list))
    def test_list_multi_volumes(self, volumes):
        tmpdir = FilePath(self.mktemp())
        tmpdir.makedirs()

        dvol = VoluminousOptions()
        for name in volumes:
            dvol.parseOptions(ARGS + ["-p", tmpdir.path, "init", name])
        dvol.parseOptions(ARGS + ["-p", tmpdir.path, "list"])

        header, rest = self._parse_list_output(dvol)
        expected_volumes = [[name, 'master'] for name in volumes]
        # `init` activates the volume, so the last initialized volume is the
        # active one.
        expected_volumes[-1] = ['*', expected_volumes[-1][0], expected_volumes[-1][1]]
        self.assertEqual(['VOLUME', 'BRANCH', 'CONTAINERS'], header)
        self.assertEqual(
            sorted(expected_volumes),
            sorted(rest),
        )

    def test_list_current_volume_deleted(self):
        """
        If the currently selected volume has been deleted, `list`
        displays all remaining volumes and no volume is marked with '*'
        indicating that it is the currently selected volume.
        """
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "bar"])
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "rm", "-f", "bar"])
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "list"])
        header, rest = self._parse_list_output(dvol)
        expected_volumes = [["foo", "master"]]
        self.assertEqual(
            sorted(expected_volumes),
            sorted(rest),
        )

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

    @given(volume_name=volume_names(), branch_name=branch_names(),
           commit_message=text(characters(min_codepoint=1, max_codepoint=127),
           min_size=1), filename=path_segments(), content=binary())
    def test_non_standard_branch(self, volume_name, branch_name,
            commit_message, filename, content):
        """
        Checking out a new branch results in it being the current active
        branch.
        """
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

    def test_branch_already_exists(self):
        """
        Creating a branch with the same name as an existing branch
        gives an appropriate meaningful error message.
        """
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "init", "foo"])
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "commit", "-m", "commit 1"])
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "checkout", "-b", "alpha"])
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "commit", "-m", "commit 2"])
        expected_output = "Cannot create existing branch alpha"
        try:
            dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
                "checkout", "-b", "alpha"])
            self.assertEqual(dvol.voluminous.getOutput()[-1], expected_output)
        except CalledProcessErrorWithOutput, error:
            self.assertIn(expected_output, error.original.output)
            self.assertTrue(error.original.returncode != 0)

    def test_log(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "init", "foo"])
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "commit", "-m", "oi"])
        first_commit = dvol.voluminous.getOutput()[-1]
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "commit", "-m", "you"])
        second_commit = dvol.voluminous.getOutput()[-1]
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path,
            "log"])
        actual = dvol.voluminous.getOutput()[-1]
        expected = (
            "commit {second_commit}\n"
            "Author: Who knows <mystery@person>\n"
            "Date: Whenever\n"
            "\n"
            "    you\n"
            "\n"
            "commit {first_commit}\n"
            "Author: Who knows <mystery@person>\n"
            "Date: Whenever\n"
            "\n"
            "    oi\n").format(
                first_commit=first_commit,
                second_commit=second_commit
            )
        expectedLines = expected.split("\n")
        actualLines = actual.split("\n")
        self.assertEqual(len(expectedLines), len(actualLines))
        for expected, actual in zip(
                expectedLines, actualLines):
            self.assertTrue(actual.startswith(expected))

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

    def test_branch_default_master(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "branch"])
        actual = dvol.voluminous.getOutput()[-1]
        self.assertEqual(actual.strip(), "* master")

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

    def test_remove_volume(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "init", "foo"])
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "rm", "-f", "foo"])
        self.assertEqual(dvol.voluminous.getOutput()[-1],
            "Deleting volume 'foo'")
        self.assertFalse(self.tmpdir.child("foo").exists())
        # Verify operation with `list`
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "list"])
        header, rest = self._parse_list_output(dvol)
        self.assertEqual(len(rest), 0)

    def test_remove_volume_does_not_exist(self):
        dvol = VoluminousOptions()
        try:
            dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "rm", "-f", "foo"])
            output = dvol.voluminous.getOutput()[-1]
        except CalledProcessErrorWithOutput, error:
            output = error.original.output
        self.assertIn("Volume 'foo' does not exist, cannot remove it", output)
        self.assertFalse(self.tmpdir.child("foo").exists())

    def test_remove_volume_path_separator(self):
        dvol = VoluminousOptions()
        try:
            dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "rm", "-f", "foo/bar"])
            output = dvol.voluminous.getOutput()[-1]
        except CalledProcessErrorWithOutput, error:
            output = error.original.output
        self.assertIn("Error", output)
        self.assertIn("foo/bar", output)

    @skip_if_python_version
    def test_get_set_config(self):
        """
        A configuration key can be set and then retrieved.
        """
        dvol = VoluminousOptions()
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "config", "user.name", "alice"])
        dvol.parseOptions(ARGS + ["-p", self.tmpdir.path, "config", "user.name"])
        self.assertEqual(dvol.voluminous.getOutput()[-1],
            "alice")
