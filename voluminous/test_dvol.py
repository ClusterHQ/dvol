"""
Tests for the Voluminous CLI.
"""

from twisted.trial.unittest import TestCase
from twisted.python.filepath import FilePath
from voluminous.dvol import VoluminousOptions, VolumeAlreadyExists
from twisted.python.usage import UsageError

class VoluminousTests(TestCase):
    def setUp(self):
        self.tmpdir = FilePath(self.mktemp())
        self.tmpdir.makedirs()

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
        self.assertEqual(dvol.voluminous.getOutput(), ["VOLUME   BRANCHES "])

    def test_list_multi_volumes(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"])
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo2"])
        dvol.parseOptions(["-p", self.tmpdir.path, "list"])
        self.assertEqual(dvol.voluminous.getOutput(), ["VOLUME   BRANCHES \n"
                                                       "foo      1        \n"
                                                       "foo2     1        "])

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
        commitId = dvol.voluminous.getOutput()[-1]
        commit = volume.child("commits").child(commitId)
        self.assertTrue(commit.exists())
        self.assertTrue(commit.child("file.txt").exists())
        self.assertEqual(commit.child("file.txt").getContent(), "alpha")
        volume.child("branches").child("master").child(
            "file.txt").setContent("beta")
        dvol.parseOptions(["-p", self.tmpdir.path,
            "reset", "--hard", "HEAD", "foo"])
        self.assertEqual(volume.child("branches").child("master")
                .child("file.txt").getContent(), "alpha")

    # TODO test branching uncommitted branch (it should fail)
    # TODO list commit messages
