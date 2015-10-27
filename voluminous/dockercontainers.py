import docker
from twisted.python import log

RETRIES = 5

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
                aggregated_volumes = container.get('Volumes', {}).values()
                # docker 1.8.2 seems to have new Mounts attribute, list of
                # objects.
                aggregated_volumes += [mount['Source'] for mount in container.get('Mounts', {})]
                # e.g. {u'/data': u'/var/lib/dvol/volumes/frob_mysql/branches/master'}
                for volume_path in aggregated_volumes:
                    # XXX implementation detail-y, will need refactoring when
                    # we support multiple backends
                    if volume_path.startswith("/var/lib/dvol/volumes"):
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

        def attempt_stop(container):
            for attempt in range(RETRIES):
                try:
                    self.client.stop(container['Id'])
                    return
                except:
                    if attempt < RETRIES - 1:
                        log.msg(
                            "Failed to stop container %s, retrying..." %
                                (container['Id'],))
                    else:
                        log.err(
                            None, "while trying to stop container %s" % (container,))

        for container in containers:
            attempt_stop(container)

        self.stopped[volume] = set(c['Id'] for c in containers)

    def start(self, volume):
        if volume not in self.stopped:
            raise NeverLocked("never locked %s, can't unlock it" % (volume,))
        for cid in self.stopped[volume]:
            try:
                self.client.start(cid)
            except:
                log.err(None, "while trying to start container %s" % (cid,))
        del self.stopped[volume]
