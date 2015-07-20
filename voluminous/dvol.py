"""
dvol: voluminous for Docker; Voluminuous client.

For the prototype, we can probably get away with manipulating directories
directly.
"""

from twisted.python.usage import Options, UsageError
from twisted.internet import defer
from twisted.python.filepath import FilePath
from twisted.python import log
from twisted.internet.task import react
import os
import sys

DEFAULT_BRANCH = "master"

class VolumeAlreadyExists(Exception):
    pass


class Voluminous(object):
    def output(self, s):
        self._output.append(s)
        print s

    def getOutput(self):
        return self._output

    def __init__(self, directory):
        self._directory = FilePath(directory)
        self._output = []

    def createBranch(self, name, branch):
        branchDir = self._directory.child(name).child("branches").child(branch)
        branchDir.makedirs()
        self.output("Created branch %s/%s" % (name, branch))

    def createVolume(self, name):
        if self._directory.child(name).exists():
            self.output("Error: volume %s already exists" % (name,))
            raise VolumeAlreadyExists()
        self._directory.child(name).makedirs()
        self.output("Created volume %s" % (name,))
        self.createBranch(name, DEFAULT_BRANCH)


class InitOptions(Options):
    """
    Create a volume.
    """
    def parseArgs(self, name):
        self.name = name


    def run(self, voluminous):
        voluminous.createVolume(self.name)



class CommitOptions(Options):
    """
    Create a volume.
    """
    optParameters = [
        ["message", "m", None, "Commit message"],
        ]

    def postOptions(self):
        if not self["message"]:
            raise UsageError("You must provide a commit message")


    def parseArgs(self, name):
        self.name = name


    def run(self, voluminous):
        voluminous.createVolume(self.name)



class VoluminousOptions(Options):
    """
    Voluminous volume manager.
    """
    optParameters = [
        ["pool", "p", None, "The name of the directory to use"],
        ]

    subCommands = [
        ["init", None, InitOptions, "Create a volume and its default master branch"],
        ["commit", None, CommitOptions, "Create a branch"],
        #["list-all-branches", None, ListVolumesOptions, "List all branches"],
        #["list-branches", None, ListBranchesOptions, "List branches for specific volume"],
        #["delete-branch", None, DeleteBranchOptions, "Delete a branch"],
        #["tag", None, TagOptions, "Create a tag"],
        #["list-tags", None, ListTagsOptions, "List tags"],
        #["push-branch", None, PushBranchOptions, "Push a branch to another pool"],
        ]


    def postOptions(self):
        if self.subCommand is None:
            return self.opt_help()
        if self["pool"] is None:
            # TODO untested
            homePath = FilePath(os.path.expanduser("~")).child(".dvol").child("volumes")
            if not homePath.exists():
                homePath.makedirs()
            self["pool"] = homePath.path
        self.voluminous = Voluminous(self["pool"])
        self.subOptions.run(self.voluminous)


def main(reactor, *argv):
    try:
        base = VoluminousOptions()
        d = defer.maybeDeferred(base.parseOptions, argv)
        def usageError(failure):
            failure.trap(UsageError)
            print str(failure.value)
            return # skips verbose exception printing
        d.addErrback(usageError)
        def err(failure):
            if reactor.running:
                reactor.stop()
        d.addErrback(err)
        return d
    except UsageError, errortext:
        print errortext
        print 'Try --help for usage details.'
        sys.exit(1)


def _main():
    react(main, sys.argv[1:])


if __name__ == "__main__":
    _main()
