"""
Tests for the Voluminous CLI.
"""

from twisted.trial.unittest import TestCase
from voluminous.dvol import VoluminousOptions
from twisted.python.filepath import FilePath

class VoluminousTests(TestCase):
    def setUp(self):
        self.tmpdir = FilePath(self.mktemp())
        self.tmpdir.makedirs()

    def test_create_volume(self):
        dvol = VoluminousOptions()
        dvol.parseOptions(["-p", self.tmpdir.path, "init", "foo"])
        self.assertTrue(self.tmpdir.child("foo").exists())
