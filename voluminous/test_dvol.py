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
    
    def test_create_volume_already_exists(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"])
        self.assertRaises(VolumeAlreadyExists,
                dvol.parseOptions, ["-p", self.tmpdir.path, "init", "foo"])
