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
from dockercontainers import Containers

DEFAULT_BRANCH = "master"
VOLUME_DRIVER_NAME = "dvol"

class VolumeAlreadyExists(Exception):
    pass


class NoSuchBranch(Exception):
    pass


class NoSuchCommit(Exception):
    pass


def get_table():
    table = texttable.Texttable(max_width=140)
    table.set_deco(0)
    return table


class DockerLock(object):
    def __init__(self):
        self.containers = Containers(VOLUME_DRIVER_NAME)

    def acquire(self, volume):
        self.containers.stop(volume)

    def release(self, volume):
        self.containers.start(volume)


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
    lockFactory = DockerLock

    def __init__(self, directory):
        self._directory = FilePath(directory)
        self._output = []
        self.lock = self.lockFactory()
        self.commitDatabase = JsonCommitDatabase(self._directory)

    def output(self, s):
        self._output.append(s)
        print s

    def getOutput(self):
        return self._output

    def listBranches(self):
        volume = self.volume()
        volumePath = self._directory.child(volume)
        branches = volumePath.child("branches").children()
        currentBranch = self.getActiveBranch(volume)
        self.output("\n".join(sorted(
            ("*" if b.basename() == currentBranch else " ")
            + " " + b.basename() for b in branches if b.isdir())))

    def checkoutBranch(self, branch, create):
        """
        "Check out" a branch, restarting containers in process, creating it
        from current branch HEAD if requested.
        """
        volume = self.volume()
        volumePath = self._directory.child(volume)
        branchPath = volumePath.child("branches").child(branch)
        if create:
            if branchPath.exists():
                self.output("Cannot create existing branch %s" % (branch,))
                return
            else:
                # Copy metadata
                meta = self.commitDatabase.read(volume,
                        self.getActiveBranch(volume))
                self.commitDatabase.write(volume, branch, meta)
                # Then copy latest HEAD of branch into new branch data
                # directory
                try:
                    HEAD = self._resolveNamedCommitCurrentBranch("HEAD", volume)
                except IndexError:
                    self.output("You must commit ('dvol commit') before you can "
                                "branch ('dvol checkout -b')")
                    return
                volumePath.child("commits").child(HEAD).copyTo(branchPath)
        else:
            if not branchPath.exists():
                self.output("Cannot switch to non-existing branch %s" % (branch,))
                return
        # Got here, so switch to the (maybe new branch)
        self.setActiveBranch(volume, branch)

    def createBranch(self, volume, branch):
        branchDir = self._directory.child(volume).child("branches").child(branch)
        branchDir.makedirs()
        self.output("Created branch %s/%s" % (volume, branch))

    def createVolume(self, name):
        if self._directory.child(name).exists():
            self.output("Error: volume %s already exists" % (name,))
            raise VolumeAlreadyExists()
        self._directory.child(name).makedirs()
        self.setActiveVolume(name)
        self.output("Created volume %s" % (name,))
        self.createBranch(name, DEFAULT_BRANCH)

    def setActiveVolume(self, volume):
         self._directory.child(
            "current_volume.json").setContent(
                json.dumps(dict(current_volume=volume)))

    def volume(self):
        currentVolume = self._directory.child("current_volume.json")
        if currentVolume.exists():
            volume = json.loads(currentVolume.getContent())["current_volume"]
        else:
            raise UsageError("No active volume: use dvol switch to choose one")
        if not self._directory.child(volume).exists():
            raise UsageError("Active volume %s does not exist: "
                             "use dvol switch to choose another" % (volume,))
        return volume

    def setActiveBranch(self, volume, branch):
        self._directory.child(volume).child(
            "current_branch.json").setContent(
                json.dumps(dict(current_branch=branch)))
        self.lock.acquire(volume)
        try:
            self.updateRunningPoint(volume)
        finally:
            self.lock.release(volume)

    def getActiveBranch(self, volume):
        currentBranch = self._directory.child(self.volume()).child("current_branch.json")
        if currentBranch.exists():
            return json.loads(currentBranch.getContent())["current_branch"]
        else:
            return DEFAULT_BRANCH

    def updateRunningPoint(self, volume):
        """
        construct a stable (wrt switching branches) path with symlinks
        """
        volumePath = self._directory.child(volume)
        branchName = self.getActiveBranch(volume)
        branchPath = volumePath.child("branches").child(branchName)
        stablePath = volumePath.child("running_point")
        if stablePath.exists():
            stablePath.remove()
        branchPath.linkTo(stablePath)
        return stablePath.path

    def commitVolume(self, message):
        volume = self.volume()
        commitId = (str(uuid.uuid4()) + str(uuid.uuid4())).replace("-", "")[:40]
        self.output(commitId)
        volumePath = self._directory.child(volume)
        branchName = self.getActiveBranch(volume)
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
        table.set_cols_align(["l", "l", "l"])
        dc = self.lock.containers # XXX ugly
        volumes = [c for c in self._directory.children() if c.isdir()]
        activeVolume = None
        if volumes:
            activeVolume = self.volume()
        rows = [["", "", ""]] + [
                ["  VOLUME", "BRANCH", "CONTAINERS"]] + [
                [("*" if c.basename() == activeVolume else " ") + " " + c.basename(),
                    # XXX support multiple branches
                    DEFAULT_BRANCH,
                    ",".join(c['Name'] for c in dc.get_related_containers(c.basename()))]
                    for c in volumes]
        table.add_rows(rows)
        self.output(table.draw())

    def listCommits(self, branch=None):
        if branch is None:
            branch = self.getActiveBranch(self.volume())
        volume = self.volume()
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

    def _resolveNamedCommitCurrentBranch(self, commit, volume):
        branch = self.getActiveBranch(volume)
        remainder = commit[len("HEAD"):]
        if remainder == "^" * len(remainder):
            offset = len(remainder)
        else:
            raise UsageError("Malformed commit identifier %r" % (commit,))
        commits = self.commitDatabase.read(volume, branch)
        # commits are appended to, so the last one is the latest
        return commits[-1 - offset]["id"]

    def _destroyNewerCommits(self, commit, volume):
        branch = self.getActiveBranch(volume)
        commits = self.commitDatabase.read(volume, branch)
        commitIndex = [c["id"] for c in commits].index(commit) + 1
        remainingCommits = commits[:commitIndex]
        destroyCommits = commits[commitIndex:]
        # TODO in the future, we'll care more about the following being an
        # atomic operation
        for commit in destroyCommits:
            volumePath = self._directory.child(volume)
            commitPath = volumePath.child("commits").child(commit["id"])
            commitPath.remove()
        self.commitDatabase.write(volume, branch, remainingCommits)

    def resetVolume(self, commit):
        """
        Forcefully roll back the current working copy to this commit,
        destroying any later commits.
        """
        # XXX tests for acquire/release
        volume = self.volume()
        volumePath = self._directory.child(volume)
        branchName = self.getActiveBranch(volume)
        branchPath = volumePath.child("branches").child(branchName)
        if commit.startswith("HEAD"):
            try:
                commit = self._resolveNamedCommitCurrentBranch(commit, volume)
            except IndexError:
                self.output("Referenced commit does not exist; check dvol log")
                return
        commitPath = volumePath.child("commits").child(commit)
        if not commitPath.exists():
            raise NoSuchCommit("commit '%s' does not exist" % (commit,))
        self.lock.acquire(volume)
        try:
            branchPath.remove()
            commitPath.copyTo(branchPath)
            self._destroyNewerCommits(commit, volume)
        finally:
            self.lock.release(volume)


class LogOptions(Options):
    """
    List commits.
    """

    def run(self, voluminous):
        voluminous.listCommits()


class InitOptions(Options):
    """
    Create a volume.
    """

    synopsis = "<volume>"

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

    def postOptions(self):
        if not self["message"]:
            raise UsageError("You must provide a commit message")

    def run(self, voluminous):
        voluminous.commitVolume(self["message"])


class ResetOptions(Options):
    """
    Reset a branch to a commit.
    """
    optFlags = [
        ["hard", None, "Force removal of newer data (must be set)"],
        ]

    synopsis = "<commit-id-or-HEAD[^*]>"

    def postOptions(self):
        if not self["hard"]:
            raise UsageError("Please specify --hard to confirm you intend to "
                    "lose data (to save your state, commit and branch, then "
                    "come back to reset)")

    def parseArgs(self, commit):
        self.commit = commit

    def run(self, voluminous):
        voluminous.resetVolume(self.commit)


class ListVolumesOptions(Options):
    """
    List volumes.
    """
    def run(self, voluminous):
        voluminous.listVolumes()


class BranchOptions(Options):
    """
    List branches.
    """

    def run(self, voluminous):
        voluminous.listBranches()


class CheckoutOptions(Options):
    """
    Switch and optionally create branches.
    """
    optFlags = [
        ["branch", "b", "Create branch"],
        ]

    synopsis = "<branch>"

    def parseArgs(self, branch):
        self.branch = branch

    def run(self, voluminous):
        voluminous.checkoutBranch(self.branch, create=self["branch"])

class SwitchOptions(Options):
    """
    Switch currently active volume.
    """
    def parseArgs(self, volume):
        self.volume = volume

    def run(self, voluminous):
        voluminous.setActiveVolume(self.volume)

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
            "Create a volume and its default master branch, then switch to it"],
        ["commit", None, CommitOptions,
            "Create a commit on the current volume and branch"],
        ["log", None, LogOptions,
            "List commits on the current volume and branch"],
        ["reset", None, ResetOptions,
            "Reset a branch to a given commit, throwing away more recent data"],
        ["branch", None, BranchOptions,
            "List branches for specific volume"],
        ["checkout", None, CheckoutOptions,
            "Switch or create branches on the current volume"],
        ["switch", None, SwitchOptions,
            "Switch current active volume"],
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
        def systemExit(failure):
            failure.trap(SystemExit)
            return # skips verbose exception printing
        d.addErrback(systemExit)
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
