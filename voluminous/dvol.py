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
import sys
import uuid
import texttable
import json

DEFAULT_BRANCH = "master"

class VolumeAlreadyExists(Exception):
    pass


def get_table():
    table = texttable.Texttable(max_width=140)
    table.set_deco(0)
    return table


class NullLock(object):
    # consider using docker pause/unpause to avoid potential issues around
    # stop/start ordering of linked containers (this could also help us
    # snapshot distributed databases...)
    def acquire(self, volume):
        pass

    def release(self, volume):
        pass


class JsonCommitDatabase(object):
    def __init__(self, directory):
        self._directory = directory

    def _getCommitDB(self, volume, branch):
        volume = self._directory.child(volume).child("branches")
        commits = volume.child("%s.json" % (branch,))
        return commits

    def read(self, volume, branch):
        commits = self._getCommitDB(volume, branch)
        if not commits.exists():
            return []
        commitData = json.loads(commits.getContent())
        return commitData

    def write(self, volume, branch, commitData):
        serialized = json.dumps(commitData)
        commits = self._getCommitDB(volume, branch)
        commits.setContent(serialized)


class Voluminous(object):
    def __init__(self, directory):
        self._directory = FilePath(directory)
        self._output = []
        self.lock = NullLock()
        self.commitDatabase = JsonCommitDatabase(self._directory)

    def output(self, s):
        self._output.append(s)
        print s

    def getOutput(self):
        return self._output

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

    def getVolumeCurrentBranch(self, volume):
        # TODO make "master" not hard-coded, fetch it from some metadata
        branchName = DEFAULT_BRANCH
        return branchName

    def getVolumeCurrentBranchPath(self, volume):
        volumePath = self._directory.child(volume)
        branchName = self.getVolumeCurrentBranch(volume)
        branchPath = volumePath.child("branches").child(branchName)
        return branchPath.path

    def commitVolume(self, volume, message):
        commitId = (str(uuid.uuid4()) + str(uuid.uuid4())).replace("-", "")[:40]
        self.output(commitId)
        volumePath = self._directory.child(volume)
        branchName = self.getVolumeCurrentBranch(volume)
        branchPath = volumePath.child("branches").child(branchName)
        commitPath = volumePath.child("commits").child(commitId)
        if commitPath.exists():
            raise Exception("woah, random uuid collision. try again!")
        commitPath.makedirs()
        # acquire lock (read: stop containers) to ensure consistent snapshot
        # with file-copy based backend
        # XXX tests for acquire/release
        self.lock.acquire(volume)
        try:
            branchPath.copyTo(commitPath)
        finally:
            self.lock.release(volume)
        self._recordCommit(volume, branchName, commitId, message)

    def _recordCommit(self, volume, branch, commitId, message):
        commitData = self.commitDatabase.read(volume, branch)
        commitData.append(dict(id=commitId, message=message))
        self.commitDatabase.write(volume, branch, commitData)

    def exists(self, volume):
        volumePath = self._directory.child(volume)
        return volumePath.exists()

    def listVolumes(self):
        table = get_table()
        table.set_cols_align(["l", "l"])
        # TODO add list of which containers are/were using the volume
        # TODO list the branches, rather than just the number of them
        rows = [["", ""]] + [
                ["VOLUME", "BRANCHES"]] + [
                [c.basename(),
                    str(len(c.child("branches").children()))]
                    for c in self._directory.children()]
        table.add_rows(rows)
        self.output(table.draw())

    def listCommits(self, volume, branch):
        aggregate = []
        for commit in reversed(self.commitDatabase.read(volume, branch)):
            # TODO fill in author/date
            aggregate.append(
                "commit %(id)s\n"
                "Author: Who knows <mystery@person>\n"
                "Date: Whenever\n"
                "\n"
                "    %(message)s\n" % commit)
        self.output("\n".join(aggregate))

    def _resolveNamedCommit(self, commit, volume):
        # TODO make "master" not hard-coded, fetch it from some metadata
        branch = DEFAULT_BRANCH
        commits = self.commitDatabase.read(volume, branch)
        # commits are appended to, so the last one is the latest
        return commits[-1]["id"]

    def resetVolume(self, commit, volume):
        """
        Forcefully roll back the current working copy to this commit.
        """
        # XXX tests for acquire/release
        volumePath = self._directory.child(volume)
        branchName = self.getVolumeCurrentBranch(volume)
        branchPath = volumePath.child("branches").child(branchName)
        if commit == "HEAD":
            commit = self._resolveNamedCommit(commit, volume)
        commitPath = volumePath.child("commits").child(commit)
        self.lock.acquire(volume)
        try:
            # TODO test the behaviour of the following commands when bind-mount
            # is in place (only matters if we pause/unpause, rather than
            # stop/start containers probably)
            branchPath.remove()
            commitPath.copyTo(branchPath)
        finally:
            self.lock.release(volume)


class LogOptions(Options):
    """
    List commits.
    """

    synopsis = "<volume-name> [<branch-name>]"

    def parseArgs(self, name, branch=DEFAULT_BRANCH):
        self.name = name
        self.branch = branch

    def run(self, voluminous):
        voluminous.listCommits(self.name, self.branch)


class InitOptions(Options):
    """
    Create a volume.
    """

    synopsis = "<volume-name>"

    def parseArgs(self, name):
        self.name = name

    def run(self, voluminous):
        voluminous.createVolume(self.name)


class CommitOptions(Options):
    """
    Create a commit.
    """
    optParameters = [
        ["message", "m", None, "Commit message"],
        ]

    synopsis = "<volume-name>"

    def postOptions(self):
        if not self["message"]:
            raise UsageError("You must provide a commit message")

    def parseArgs(self, name):
        self.name = name

    def run(self, voluminous):
        voluminous.commitVolume(self.name, message=self["message"])


class ResetOptions(Options):
    """
    Reset a branch to a commit.
    """
    optFlags = [
        ["hard", None, "Force removal of newer data (must be set)"],
        ]

    synopsis = "<commit-id-or-HEAD>"

    def postOptions(self):
        if not self["hard"]:
            raise UsageError("Please specify --hard to confirm you intend to "
                    "lose data (to save your state, commit and branch, then "
                    "come back to reset)")

    def parseArgs(self, commit, volume):
        self.commit = commit
        self.volume = volume

    def run(self, voluminous):
        voluminous.resetVolume(self.commit, self.volume)


class ListVolumesOptions(Options):
    """
    List volumes.
    """
    def run(self, voluminous):
        voluminous.listVolumes()


class VoluminousOptions(Options):
    """
    Voluminous volume manager.
    """
    optParameters = [
        ["pool", "p", None, "The name of the directory to use"],
        ]

    subCommands = [
        ["list", None, ListVolumesOptions,
            "List all volumes"],
        ["init", None, InitOptions,
            "Create a volume and its default master branch"],
        ["commit", None, CommitOptions,
            "Create a commit"],
        ["log", None, LogOptions,
            "List commits on a branch"],
        ["reset", None, ResetOptions,
            "Reset a branch to a given commit, throwing away more recent data"],
        #["list-branches", None, ListBranchesOptions, "List branches for specific volume"],
        #["delete-branch", None, DeleteBranchOptions, "Delete a branch"],
        #["tag", None, TagOptions, "Create a tag"],
        #["push-branch", None, PushBranchOptions, "Push a branch to another pool"],
        ]


    def postOptions(self):
        if self.subCommand is None:
            return self.opt_help()
        if self["pool"] is None:
            # TODO untested
            homePath = FilePath("/var/lib/dvol/volumes")
            if not homePath.exists():
                homePath.makedirs()
            self["pool"] = homePath.path
        self.voluminous = Voluminous(self["pool"])
        self.subOptions.run(self.voluminous)


# TODO untested below
def _main(reactor, *argv):
    try:
        base = VoluminousOptions()
        d = defer.maybeDeferred(base.parseOptions, argv)
        def usageError(failure):
            failure.trap(UsageError)
            print str(failure.value)
            return # skips verbose exception printing
        d.addErrback(usageError)
        def err(failure):
            # following line is debug only
            log.err(failure)
            if reactor.running:
                reactor.stop()
        d.addErrback(err)
        return d
    except UsageError, errortext:
        print errortext
        print 'Try --help for usage details.'
        sys.exit(1)


def main():
    react(_main, sys.argv[1:])


if __name__ == "__main__":
    main()
