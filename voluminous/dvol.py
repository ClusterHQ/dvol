"""
dvol: voluminous for Docker; Voluminuous client.

For the prototype, we can probably get away with manipulating directories
directly.
"""

from twisted.python.usage import Options, UsageError
from twisted.python.filepath import FilePath

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
        self._directory.child(name).child("branches").child(branch).makedirs()
        self.output("Created branch %s/%s" % (name, branch))

    def createVolume(self, name):
        if self._directory.child(name).exists():
            self.output("Error: volume %s already exists" % (name,))
            raise VolumeAlreadyExists()
        self._directory.child(name).makedirs()
        self.output("Created volume %s" % (name,))
        self.createBranch(name, DEFAULT_BRANCH)


class CreateOptions(Options):
    """
    Create a volume.
    """
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
        ["init", None, CreateOptions, "Create a volume and its default master branch"],
        #["list-all-branches", None, ListVolumesOptions, "List all branches"],
        #["branch", None, BranchOptions, "Create a branch"],
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
            raise UsageError("pool is required")
        self.voluminous = Voluminous(self["pool"])
        self.subOptions.run(self.voluminous)
