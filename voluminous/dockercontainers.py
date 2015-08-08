import docker
from twisted.python import log

class NeverLocked(Exception):
    pass

class AlreadyLocked(Exception):
    pass

class Containers(object):
    """
    Operations on the set of containers which pertain to dvol.  Also maintain
    state on which containers we stopped so that we can start them again.

    @ivar stopped: mapping from volume name for which we stopped containers to
        set of container ids, so that we can attempt to start them again.
    """
    def __init__(self, volume_driver_name):
        self.volume_driver_name = volume_driver_name
        self.stopped = dict()
        self.client = docker.client.Client()

    def get_related_containers(self, volume):
        """
        Find running containers using the dvol plugin that are using the given
        volume.
        """
        all_containers = self.client.containers()
        containers = []
        for container in all_containers:
            # race condition: a container is deleted during the following
            # iteration; catch and log exceptions but otherwise ignore; this is
            # a best-effort snapshot of current docker state
            try:
                container = self.client.inspect_container(container['Id'])
                volume_driver_matches = (
                        container['Config']['VolumeDriver'] == self.volume_driver_name)
                running = container['State']['Running']
                using_volume = False
                # e.g. {u'/data': u'/var/lib/dvol/volumes/frob_mysql/branches/master'}
                for volume_path in container['Volumes'].itervalues():
                    # XXX implementation detail-y, will need refactoring when
                    # we support multiple backends
                    parts = volume_path.split("/")
                    volume_name = parts[-3]
                    if volume_name == volume:
                        using_volume = True
                if volume_driver_matches and running and using_volume:
                    containers.append(container)
            except:
                log.err(None, "while fetching container state %s, "
                              "maybe it was deleted" % (container['Id'],))
        return containers

    def stop(self, volume):
        """
        Stop containers which are using this volume, and remember which
        containers were stopped.
        """
        if volume in self.stopped:
            raise AlreadyLocked("already locked %s, can't lock it" % (volume,))
        containers = self.get_related_containers(volume)
        self.stopped[volume] = set()
        for container in containers:
            try:
                self.client.pause(container['Id'])
            except:
                log.err(None, "while trying to stop container %s" % (container,))
        self.stopped[volume] = set(c['Id'] for c in containers)

    def start(self, volume):
        if volume not in self.stopped:
            raise NeverLocked("never locked %s, can't unlock it" % (volume,))
        for cid in self.stopped[volume]:
            try:
                self.client.unpause(cid)
            except:
                log.err(None, "while trying to start container %s" % (cid,))
        del self.stopped[volume]
