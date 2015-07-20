"""
dvol: voluminous for Docker; Voluminuous client.

For the prototype, we can probably get away with manipulating directories
directly.
"""

from twisted.python.usage import Options, UsageError
from twisted.python.filepath import FilePath


class Voluminous(object):
    def __init__(self, directory):
        self._directory = FilePath(directory)

    def createVolume(self, name):
        # TODO raise if already exists
        self._directory.child(name).makedirs()


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
        self.subOptions.run(Voluminous(self["pool"]))
