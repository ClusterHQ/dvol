"""
dvol: voluminous for Docker; Voluminuous client.

For the prototype, we can probably get away with manipulating directories
directly.
"""

from twisted.python.usage import Options, UsageError
from twisted.internet import defer
from twisted.python.filepath import (
    FilePath,
    InsecurePath,
)
from twisted.python import log
from twisted.internet.task import react
import sys
import uuid
import texttable
import json
import yaml
import os
import subprocess
from dockercontainers import Containers

DEFAULT_BRANCH = "master"
VOLUME_DRIVER_NAME = "dvol"
PWD_PATH = FilePath("/pwd")

def copyTo(fromPath, toPath):
    """
    Copy the contents of fromPath to toPath, assuming a quiesced filesystem,
    and that toPath doesn't exist, in a way that doesn't fail to copy special
    files like FIFOs.
    """
    if toPath.exists():
        raise Exception(
            "Cannot copy %(fromPath)s to %(toPath)s because it exists" %
            dict(toPath=toPath.path, fromPath=fromPath.path))
    subprocess.check_call(["cp", "-a", fromPath.path, toPath.path])
    os.chmod(toPath.path, 0777) # TODO add tests

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


class EmptyContainers(object):
    def get_related_containers(self, volume):
        return []

    def remove_related_containers(self, volume):
        pass

class NullLock(object):
    containers = EmptyContainers()
    def acquire(self, volume):
        return
    def release(self, volume):
        return


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
    def __init__(self, directory, lockFactory=DockerLock):
        self._directory = FilePath(directory)
        self._output = []
        self.lock = lockFactory()
        self.commitDatabase = JsonCommitDatabase(self._directory)

    def output(self, s):
        self._output.append(s)
        print s

    def getOutput(self):
        result =["\n".join(self._output)]
        self._output = []
        return result

    def allBranches(self, volume):
        volumePath = self._directory.child(volume)
        branches = volumePath.child("branches").children()
        return [b.basename() for b in branches if b.isdir()]

    def listBranches(self):
        volume = self.volume()
        branches = self.allBranches(volume)
        currentBranch = self.getActiveBranch(volume)
        self.output("\n".join(sorted(
            ("*" if b == currentBranch else " ")
            + " " + b for b in branches)))

    def checkoutBranch(self, branch, create):
        """
        "Check out" a branch, restarting containers in process, creating it
        from current branch HEAD if requested.
        """
        volume = self.volume()
        volumePath = self._directory.child(volume)
        # this raises an exception if branch is not a valid path segment
        branchPath = volumePath.child("branches").child(branch)
        if create:
            if branchPath.exists():
                self.output("Cannot create existing branch %s" % (branch,))
                return
            else:
                try:
                    HEAD = self._resolveNamedCommitCurrentBranch("HEAD", volume)
                except IndexError:
                    self.output("You must commit ('dvol commit') before you can "
                                "branch ('dvol checkout -b')")
                    return
                # Copy metadata
                meta = self.commitDatabase.read(volume,
                        self.getActiveBranch(volume))
                self.commitDatabase.write(volume, branch, meta)
                # Then copy latest HEAD of branch into new branch data
                # directory
                copyTo(volumePath.child("commits").child(HEAD), branchPath)
        else:
            if not branchPath.exists():
                self.output("Cannot switch to non-existing branch %s" % (branch,))
                return
        # Got here, so switch to the (maybe new branch)
        self.setActiveBranch(volume, branch)

    def createBranch(self, volume, branch):
        branchDir = self._directory.child(volume).child("branches").child(branch)
        branchDir.makedirs()
        # This branchDir is the one which will be bind-mounted into running
        # containers, via a symlink, but with symlinks and docker bind-mounts
        # it seems that it's the permissions of the target which affects the
        # (e.g.) writeability of the resulting mount.
        # Because some containers have processes which run as non-root users,
        # make the volume world-writeable so that it can still be useful to
        # those processes. In the future, it might be better to have options
        # for which uid, gid and perms the volume should have. This is
        # effectively the same as `chmod a=rwx branchDir.path`.
        os.chmod(branchDir.path, 0777)
        self.output("Created branch %s/%s" % (volume, branch))

    def createVolume(self, name):
        try:
            # XXX: Behaviour around names with relative path identifiers
            # such as '..' and '.' is largely undefined, these should
            # probably be rejected outright.
            if self._directory.child(name).exists():
                self.output("Error: volume %s already exists" % (name,))
                return
        except InsecurePath:
            self.output("Error: %s is not a valid name" % (name,))
            return
        self._directory.child(name).makedirs()
        self.setActiveVolume(name)
        self.output("Created volume %s" % (name,))
        self.createBranch(name, DEFAULT_BRANCH)

    def removeVolume(self, volume, force=False):
        try:
            if not self._directory.child(volume).exists():
                self.output("Volume %r does not exist, cannot remove it" %
                        (volume,))
                return
        except InsecurePath:
            self.output("Error: %s is not a valid name" % (volume,))
            return
        containers = self.lock.containers.get_related_containers(volume)
        if containers:
            raise UsageError("Cannot remove %r while it is in use by '%s'" %
                    (volume, (",".join(c['Name'] for c in containers))))
        if force or self._userIsSure("This will remove all containers using the volume"):
            self.output("Deleting volume %r" % (volume,))
            # Remove related containers
            self.lock.containers.remove_related_containers(volume)
            self._directory.child(volume).remove()

        else:
            self.output("Aborting.")

    def deleteBranch(self, branch):
        volume = self.volume()
        if branch == self.getActiveBranch(volume):
            raise UsageError("Cannot delete active branch, use "
                             "'dvol checkout' to switch branches first")
        if branch not in self.allBranches(volume):
            raise UsageError("Branch %r does not exist" % (branch,))
        if self._userIsSure():
            self.output("Deleting branch %r" % (branch,))
            volumePath = self._directory.child(volume)
            branchPath = volumePath.child("branches").child(branch)
            branchPath.remove()
        else:
            self.output("Aborting.")

    def _userIsSure(self, extraMessage=None):
        message = "Are you sure? "
        if extraMessage:
            message += extraMessage
        message += " (y/n): "
        sys.stdout.write(message)
        sys.stdout.flush()
        return raw_input().lower() in ("y", "yes")

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
        currentBranch = self._directory.child(volume).child("current_branch.json")
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
        # Make the commits directory if necessary
        if not commitPath.parent().exists():
            commitPath.parent().makedirs()
        # acquire lock (read: stop containers) to ensure consistent snapshot
        # with file-copy based backend
        # XXX tests for acquire/release
        self.lock.acquire(volume)
        try:
            copyTo(branchPath, commitPath)
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
        volumes = [v for v in self._directory.children() if v.isdir()]
        activeVolume = None
        if volumes:
            try:
                activeVolume = self.volume()
            except UsageError:
                # don't refuse to list volumes just because none of them are active
                pass
        rows = [["", "", ""]] + [
                ["  VOLUME", "BRANCH", "CONTAINERS"]] + [
                [("*" if v.basename() == activeVolume else " ") + " " + v.basename(),
                    self.getActiveBranch(v.basename()),
                    ",".join(c['Name'] for c in dc.get_related_containers(v.basename()))]
                    for v in sorted(volumes)]
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
        # TODO in the future, we'll care more about the following being an
        # atomic operation
        branch = self.getActiveBranch(volume)
        commits = self.commitDatabase.read(volume, branch)
        commitIndex = [c["id"] for c in commits].index(commit) + 1
        remainingCommits = commits[:commitIndex]
        destroyCommits = commits[commitIndex:]
        # look in all branches for commit references before removing them
        totalCommits = set()
        for otherBranch in self.allBranches(volume):
            if otherBranch == branch:
                # skip this branch, otherwise we'll never destroy any commits
                continue
            commits = self.commitDatabase.read(volume, branch)
            totalCommits.update(commit["id"] for commit in commits)
        for commit in destroyCommits:
            commitId = commit["id"]
            if commitId in totalCommits:
                # skip destroying this commit; it is still actively referred to
                # in another branch
                continue
            volumePath = self._directory.child(volume)
            commitPath = volumePath.child("commits").child(commitId)
            commitPath.remove()
        self.commitDatabase.write(volume, branch, remainingCommits)

    def resetVolume(self, commit):
        """
        Forcefully roll back the current working copy to this commit,
        destroying any later commits.
        """
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
            copyTo(commitPath, branchPath)
            self._destroyNewerCommits(commit, volume)
        finally:
            self.lock.release(volume)

    def seedVolumes(self, compose_file):
        # XXX: does not work with absolute paths, but should
        compose = yaml.load(PWD_PATH.child(compose_file).open())
        valid_volumes = []
        # TODO: will need updating for new compose file format
        for service, config in compose.iteritems():
            if "volume_driver" in config and config["volume_driver"] == "dvol":
                for volume in config["volumes"]:
                    if ":" in volume and not volume.startswith("/"):
                        valid_volumes.append((volume, config))
        if not valid_volumes:
            self.output('No volumes found with "volume_driver: dvol" and a named volume (like "volumename:/path_inside_container")! Please check your docker-compose.yml file.')
        else:
            self.output("Please seed your dvol volume(s) by running the following command(s):")
        for volume, config in valid_volumes:
            # TODO: need some validation before running commands with string interpolation here, docker-compose file could be malicious
            # TODO: would be better if we ran the command for the user, rather than making them copy and paste
            self.output("docker run --volume-driver=dvol -v %(volume)s:/_target -ti %(image)s sh -c 'cp -av %(source)s/* /_target/'" % dict(
                    volume=volume.split(":")[0],
                    source=volume.split(":")[1],
                    image=config["image"],))


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


class SeedOptions(Options):
    """
    Seed some volumes.
    """

    synopsis = "<docker-compose-file-in-current-directory>"

    def parseArgs(self, filename):
        self.filename = filename

    def run(self, voluminous):
        voluminous.seedVolumes(self.filename)


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
    List or delete branches.
    """
    optParameters = [
        ["delete", "d", None, "Delete specified branch"],
        ]

    def run(self, voluminous):
        if self["delete"]:
            voluminous.deleteBranch(self["delete"])
        else:
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

class RemoveOptions(Options):
    """
    Entirely destroy a volume.
    """
    optFlags = [
        ["force", "f", "Force remove"],
        ]

    synopsis = "<force>"
    
    def parseArgs(self, volume):
        self.volume = volume

    def run(self, voluminous):
        voluminous.removeVolume(self.volume, force=self["force"])

class VoluminousOptions(Options):
    """
    Voluminous volume manager.
    """
    optFlags = [
        ["disable-docker-integration", None,
            "Do not attempt to list/stop/start docker containers "
            "which are using dvol volumes",]
        ]

    optParameters = [
        ["pool", "p", None, "The name of the directory to use"],
        ]

    subCommands = [
        ["list", None, ListVolumesOptions,
            "List all dvol volumes"],
        ["ls", None, ListVolumesOptions,
            "Same as 'list'"],
        ["init", None, InitOptions,
            "Create a volume and its default master branch, then switch to it"],
        ["seed", None, SeedOptions,
            "Create a set of volumes with default data extracted from the docker images referenced in a docker compose file"],
        ["switch", None, SwitchOptions,
            "Switch active volume for commands below (commit, log etc)"],
        ["rm", None, RemoveOptions,
            "Destroy a dvol volume"],
        ["commit", None, CommitOptions,
            "Create a commit on the active volume and branch"],
        ["log", None, LogOptions,
            "List commits on the active volume and branch"],
        ["reset", None, ResetOptions,
            "Reset active branch to a commit, destroying later unreferenced commits"],
        ["branch", None, BranchOptions,
            "List or delete branches for active volume"],
        ["checkout", None, CheckoutOptions,
            "Check out or create branches on the active volume"],
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

        lockFactory = DockerLock
        if self["disable-docker-integration"]:
            # Do not attempt to connect to Docker if we've been asked not to.
            lockFactory = NullLock

        self.voluminous = Voluminous(self["pool"], lockFactory=lockFactory)
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
