"""
Tests for the Voluminous CLI.
"""

from twisted.trial.unittest import TestCase
from voluminous.dvol import VoluminousOptions

class VoluminousTests(TestCase):
    def test_create_volume(self):
        dvol = VoluminousOptions()
        import pdb; pdb.set_trace()
        dvol.parseArgs("create", "-p", self.tmpdir(), "foo")
        dvol.run()
