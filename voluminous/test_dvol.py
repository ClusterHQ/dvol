"""
Tests for the Voluminous CLI.
"""

from twisted.trial.unittest import TestCase
from twisted.python.filepath import FilePath
from voluminous.dvol import VoluminousOptions, VolumeAlreadyExists, Voluminous
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

class VoluminousTests(TestCase):
    def setUp(self):
        self.tmpdir = FilePath(self.mktemp())
        self.tmpdir.makedirs()
        self.patch(Voluminous, "lockFactory", NullLock)

    def test_create_volume(self):
        # TODO test volume names with '/' in them - they should not end up
        # making nested heirarchy
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"])
        self.assertTrue(self.tmpdir.child("foo").exists())
        self.assertTrue(self.tmpdir.child("foo").child("branches")
                .child("master").exists())
        self.assertEqual(dvol.voluminous.getOutput(),
                ["Created volume foo", "Created branch foo/master"])

    def test_create_volume_already_exists(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"])
        self.assertRaises(VolumeAlreadyExists,
                dvol.parseOptions, ["-p", self.tmpdir.path, "init", "foo"])
        self.assertEqual(dvol.voluminous.getOutput(),
                ["Error: volume foo already exists"])

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
            "commit", "-m", "hello from 30,000 ft", "foo"])
        commitId = dvol.voluminous.getOutput()[-1]
        commit = volume.child("commits").child(commitId)
        self.assertTrue(commit.exists())
        self.assertTrue(commit.child("file.txt").exists())
        self.assertEqual(commit.child("file.txt").getContent(), "hello!")

    def test_list_empty_volumes(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "list"])
        self.assertEqual(dvol.voluminous.getOutput(), ["VOLUME   BRANCH   CONTAINERS "])

    def test_list_multi_volumes(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"])
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo2"])
        dvol.parseOptions(["-p", self.tmpdir.path, "list"])
        self.assertEqual(dvol.voluminous.getOutput(), ["VOLUME   BRANCH   CONTAINERS \n"
                                                       "foo      master              \n"
                                                       "foo2     master              "])

    def test_log(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path,
            "init", "foo"])
        dvol.parseOptions(["-p", self.tmpdir.path,
            "commit", "-m", "oi", "foo"])
        dvol.parseOptions(["-p", self.tmpdir.path,
            "commit", "-m", "you",  "foo"])
        dvol.parseOptions(["-p", self.tmpdir.path,
            "log", "foo", "master"])
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
            "commit", "-m", "commit 1", "foo"])
        commitId = dvol.voluminous.getOutput()[-1]
        print "commitId", commitId
        commit = volume.child("commits").child(commitId)
        self.assertTrue(commit.exists())
        self.assertTrue(commit.child("file.txt").exists())
        self.assertEqual(commit.child("file.txt").getContent(), "alpha")
        volume.child("branches").child("master").child(
            "file.txt").setContent("beta")
        dvol.parseOptions(["-p", self.tmpdir.path,
            "reset", "--hard", commitId, "foo"])
        self.assertEqual(volume.child("branches").child("master")
                .child("file.txt").getContent(), "alpha")

    def test_reset_HEAD(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"])
        volume = self.tmpdir.child("foo")
        volume.child("branches").child("master").child(
            "file.txt").setContent("alpha")
        dvol.parseOptions(["-p", self.tmpdir.path,
            "commit", "-m", "commit 1", "foo"])
        volume.child("branches").child("master").child(
            "file.txt").setContent("beta")
        dvol.parseOptions(["-p", self.tmpdir.path,
            "reset", "--hard", "HEAD", "foo"])
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
            "commit", "-m", "commit 1", "foo"])

        volume.child("branches").child("master").child(
            "file.txt").setContent("alpha")
        dvol.parseOptions(["-p", self.tmpdir.path,
            "commit", "-m", "commit 2", "foo"])

        volume.child("branches").child("master").child(
            "file.txt").setContent("beta")
        dvol.parseOptions(["-p", self.tmpdir.path,
            "reset", "--hard", "HEAD", "foo"])
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
            "commit", "-m", "commit 1", "foo"])

        volume.child("branches").child("master").child(
            "file.txt").setContent("NEW")
        dvol.parseOptions(["-p", self.tmpdir.path,
            "commit", "-m", "commit 2", "foo"])

        volume.child("branches").child("master").child(
            "file.txt").setContent("NEWER")
        dvol.parseOptions(["-p", self.tmpdir.path,
            "reset", "--hard", "HEAD^", "foo"])
        # working copy is changed from beta to alpha, but not BAD
        self.assertEqual(volume.child("branches").child("master")
                .child("file.txt").getContent(), "OLD")

        # newest commit has been wiped out
        dvol.parseOptions(["-p", self.tmpdir.path,
            "log", "foo", "master"])
        actual = dvol.voluminous.getOutput()[-1]
        self.assertEqual(len(actual.split("\n")), 6) # 6 lines = 1 commit

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
            "commit", "-m", "commit 1", "foo"])

        dvol.parseOptions(["-p", self.tmpdir.path, "checkout", "-b", "newbranch"])
        actual = dvol.voluminous.getOutput()[-1]
        self.assertEqual(actual.strip(), "  newbranch\n* master")

        dvol.parseOptions(["-p", self.tmpdir.path,
            "log", "foo"])
        actual = dvol.voluminous.getOutput()[-1]
        # the commit should have been "copied" to the new branch
        self.assertEqual(len(actual.split("\n")), 6) # 6 lines = 1 commit

    def test_switch_branches_restarts_containers(self):
        1/0

    def test_rollback_branch_doesnt_delete_referenced_data_in_other_branches(self):
        1/0

    # TODO test branching uncommitted branch (it should fail)
    # TODO list commit messages
