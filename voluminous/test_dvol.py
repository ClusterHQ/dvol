"""
Tests for the Voluminous CLI.
"""

from twisted.trial.unittest import TestCase
from twisted.python.filepath import FilePath
from voluminous.dvol import VoluminousOptions, VolumeAlreadyExists

class VoluminousTests(TestCase):
    def setUp(self):
        self.tmpdir = FilePath(self.mktemp())
        self.tmpdir.makedirs()

    def test_create_volume(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"])
        self.assertTrue(self.tmpdir.child("foo").exists())
        self.assertTrue(self.tmpdir.child("foo").child("branches").child("master").exists())
        self.assertEqual(dvol.voluminous.getOutput(), ["Created volume foo", "Created branch foo/master"])

    def test_create_volume_already_exists(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"])
        self.assertRaises(VolumeAlreadyExists,
                dvol.parseOptions, ["-p", self.tmpdir.path, "init", "foo"])
        self.assertEqual(dvol.voluminous.getOutput(), ["Error: volume foo already exists"])

    def test_commit_volume(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "commit", "-m", "hello from 30,000 ft"])


