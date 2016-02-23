"""
Tests for the Voluminous CLI.
"""

from string import letters

from hypothesis import given
from hypothesis.strategies import binary, characters, dictionaries, sets, text

from twisted.trial.unittest import TestCase
from twisted.python.filepath import FilePath
from dvol import VoluminousOptions, VolumeAlreadyExists, Voluminous
from twisted.python.usage import UsageError

class EmptyContainers(object):
    def get_related_containers(self, volume):
        return []

class NullLock(object):
    containers = EmptyContainers()
    def acquire(self, volume):
        return
    def release(self, volume):
        return


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
        self.patch(Voluminous, "lockFactory", NullLock)

    def test_create_volume(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"])
        self.assertTrue(self.tmpdir.child("foo").exists())
        self.assertTrue(self.tmpdir.child("foo").child("branches")
                .child("master").exists())
        self.assertEqual(dvol.voluminous.getOutput(),
                ["Created volume foo", "Created branch foo/master"])

    def test_create_volume_already_exists(self):
        dvol = VoluminousOptions()
        # Create the repository twice, second time should have the error
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"]) 
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"])
        self.assertEqual(dvol.voluminous.getOutput(),
                ["Error: volume foo already exists"])

    def test_create_volume_with_path_seperator(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo/bar"])
        self.assertEqual(dvol.voluminous.getOutput(),
                ["Error: foo/bar is not a valid name"])

    def test_commit_no_message_raises_error(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"])
        self.assertRaises(UsageError,
                dvol.parseOptions, ["-p", self.tmpdir.path, "commit"])

    def test_commit_volume(self):
        # TODO need to assert that containers using this volume get stopped
        # and started around commits
        # TODO test snapshotting nonexistent volume
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"])
        volume = self.tmpdir.child("foo")
        volume.child("branches").child("master").child(
            "file.txt").setContent("hello!")
        dvol.parseOptions(["-p", self.tmpdir.path,
            "commit", "-m", "hello from 30,000 ft"])
        commitId = dvol.voluminous.getOutput()[-1]
        commit = volume.child("commits").child(commitId)
        self.assertTrue(commit.exists())
        self.assertTrue(commit.child("file.txt").exists())
        self.assertEqual(commit.child("file.txt").getContent(), "hello!")

    def test_list_empty_volumes(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "list"])
        self.assertEqual(dvol.voluminous.getOutput(), ["  VOLUME   BRANCH   CONTAINERS "])

    @given(volumes=sets(volume_names(), min_size=1, average_size=10).map(list))
    def test_list_multi_volumes(self, volumes):
        tmpdir = FilePath(self.mktemp())
        tmpdir.makedirs()

        dvol = VoluminousOptions()
        for name in volumes:
            dvol.parseOptions(["-p", tmpdir.path, "init", name])
        dvol.parseOptions(["-p", tmpdir.path, "list"])

        lines = dvol.voluminous.getOutput()[0].split("\n")
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
            dvol.parseOptions(["-p", tmpdir.path, "init", volume])
            dvol.parseOptions(["-p", tmpdir.path, "commit", "-m", "hello"])
            dvol.parseOptions(["-p", tmpdir.path, "checkout", "-b", branch])

        dvol.parseOptions(["-p", tmpdir.path, "list"])
        lines = dvol.voluminous.getOutput()[0].split("\n")
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
           commit_message=text(characters(max_codepoint=127), min_size=1),
           filename=path_segments(), content=binary())
    def test_non_standard_branch(self, volume_name, branch_name, commit_message, filename,
                                 content):
        tmpdir = FilePath(self.mktemp())
        tmpdir.makedirs()

        dvol = VoluminousOptions()
        dvol.parseOptions(['-p', tmpdir.path, 'init', volume_name])
        volume = tmpdir.child(volume_name)
        volume.child("branches").child("master").child(filename).setContent(content)
        dvol.parseOptions(["-p", tmpdir.path, "commit", "-m", commit_message])
        dvol.parseOptions(["-p", tmpdir.path, "checkout", "-b", branch_name])
        dvol.parseOptions(["-p", tmpdir.path, "list"])
        lines = dvol.voluminous.getOutput()[0].split("\n")
        header, rest = lines[0], lines[1:]
        self.assertEqual(['VOLUME', 'BRANCH', 'CONTAINERS'], header.split())
        self.assertEqual(
            [['*', volume_name, branch_name]], [line.split() for line in rest])

    def test_log(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path,
            "init", "foo"])
        dvol.parseOptions(["-p", self.tmpdir.path,
            "commit", "-m", "oi"])
        dvol.parseOptions(["-p", self.tmpdir.path,
            "commit", "-m", "you"])
        dvol.parseOptions(["-p", self.tmpdir.path,
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

    def test_reset(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"])
        volume = self.tmpdir.child("foo")
        volume.child("branches").child("master").child(
            "file.txt").setContent("alpha")
        dvol.parseOptions(["-p", self.tmpdir.path,
            "commit", "-m", "commit 1"])
        commitId = dvol.voluminous.getOutput()[-1]
        print "commitId", commitId
        commit = volume.child("commits").child(commitId)
        self.assertTrue(commit.exists())
        self.assertTrue(commit.child("file.txt").exists())
        self.assertEqual(commit.child("file.txt").getContent(), "alpha")
        volume.child("branches").child("master").child(
            "file.txt").setContent("beta")
        dvol.parseOptions(["-p", self.tmpdir.path,
            "reset", "--hard", commitId])
        self.assertEqual(volume.child("branches").child("master")
                .child("file.txt").getContent(), "alpha")

    def test_reset_HEAD(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"])
        volume = self.tmpdir.child("foo")
        volume.child("branches").child("master").child(
            "file.txt").setContent("alpha")
        dvol.parseOptions(["-p", self.tmpdir.path,
            "commit", "-m", "commit 1"])
        volume.child("branches").child("master").child(
            "file.txt").setContent("beta")
        dvol.parseOptions(["-p", self.tmpdir.path,
            "reset", "--hard", "HEAD"])
        # working copy is changed
        self.assertEqual(volume.child("branches").child("master")
                .child("file.txt").getContent(), "alpha")

    def test_reset_HEAD_multiple_commits(self):
        # assert that the correct (latest) commit is rolled back to
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"])
        volume = self.tmpdir.child("foo")

        volume.child("branches").child("master").child(
            "file.txt").setContent("BAD")
        dvol.parseOptions(["-p", self.tmpdir.path,
            "commit", "-m", "commit 1"])

        volume.child("branches").child("master").child(
            "file.txt").setContent("alpha")
        dvol.parseOptions(["-p", self.tmpdir.path,
            "commit", "-m", "commit 2"])

        volume.child("branches").child("master").child(
            "file.txt").setContent("beta")
        dvol.parseOptions(["-p", self.tmpdir.path,
            "reset", "--hard", "HEAD"])
        # working copy is changed from beta to alpha, but not BAD
        self.assertEqual(volume.child("branches").child("master")
                .child("file.txt").getContent(), "alpha")

    def test_reset_HEAD_hat_multiple_commits(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"])
        volume = self.tmpdir.child("foo")

        volume.child("branches").child("master").child(
            "file.txt").setContent("OLD")
        dvol.parseOptions(["-p", self.tmpdir.path,
            "commit", "-m", "commit 1"])
        oldCommit = dvol.voluminous.getOutput()[-1]

        volume.child("branches").child("master").child(
            "file.txt").setContent("NEW")
        dvol.parseOptions(["-p", self.tmpdir.path,
            "commit", "-m", "commit 2"])
        newCommit = dvol.voluminous.getOutput()[-1]

        volume.child("branches").child("master").child(
            "file.txt").setContent("NEWER")

        # both exist
        self.assertTrue(volume.child("commits").child(oldCommit).exists())
        self.assertTrue(volume.child("commits").child(newCommit).exists())

        dvol.parseOptions(["-p", self.tmpdir.path,
            "reset", "--hard", "HEAD^"])
        self.assertEqual(volume.child("branches").child("master")
                .child("file.txt").getContent(), "OLD")

        # newest commit has been wiped out
        dvol.parseOptions(["-p", self.tmpdir.path,
            "log"])
        actual = dvol.voluminous.getOutput()[-1]
        self.assertEqual(len(actual.split("\n")), 6) # 6 lines = 1 commit

        # only old exists
        self.assertTrue(volume.child("commits").child(oldCommit).exists())
        self.assertFalse(volume.child("commits").child(newCommit).exists())

    def test_branch_default_master(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"])
        dvol.parseOptions(["-p", self.tmpdir.path, "branch"])
        actual = dvol.voluminous.getOutput()[-1]
        self.assertEqual(actual.strip(), "* master")

    def test_create_branch_from_current_HEAD(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"])

        volume = self.tmpdir.child("foo")
        volume.child("branches").child("master").child(
            "file.txt").setContent("hello")
        dvol.parseOptions(["-p", self.tmpdir.path,
            "commit", "-m", "commit 1"])

        dvol.parseOptions(["-p", self.tmpdir.path,
            "checkout", "-b", "newbranch"])
        dvol.parseOptions(["-p", self.tmpdir.path, "branch"])
        actual = dvol.voluminous.getOutput()[-1]
        self.assertEqual(actual, "  master\n* newbranch")

        dvol.parseOptions(["-p", self.tmpdir.path,
            "log"])
        actual = dvol.voluminous.getOutput()[-1]
        # the commit should have been "copied" to the new branch
        self.assertEqual(len(actual.split("\n")), 6) # 6 lines = 1 commit

    def test_rollback_branch_doesnt_delete_referenced_data_in_other_branches(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"])
        volume = self.tmpdir.child("foo")

        volume.child("branches").child("master").child(
            "file.txt").setContent("OLD")
        dvol.parseOptions(["-p", self.tmpdir.path,
            "commit", "-m", "commit 1"])
        oldCommit = dvol.voluminous.getOutput()[-1]

        volume.child("branches").child("master").child(
            "file.txt").setContent("NEW")
        dvol.parseOptions(["-p", self.tmpdir.path,
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
        dvol.parseOptions(["-p", self.tmpdir.path,
            "checkout", "-b", "newbranch"])
        dvol.parseOptions(["-p", self.tmpdir.path,
            "checkout", "master"])

        dvol.parseOptions(["-p", self.tmpdir.path,
            "reset", "--hard", "HEAD^"])
        self.assertEqual(volume.child("branches").child("master")
                .child("file.txt").getContent(), "OLD")

        # newest commit has been wiped out in master branch metadata
        dvol.parseOptions(["-p", self.tmpdir.path,
            "log"])
        actual = dvol.voluminous.getOutput()[-1]
        self.assertEqual(len(actual.split("\n")), 6) # 6 lines = 1 commit

        # new still exists because it's referenced in another branch
        self.assertTrue(volume.child("commits").child(oldCommit).exists())
        self.assertTrue(volume.child("commits").child(newCommit).exists())
