import docker
from twisted.python import log

class NeverLocked(Exception):
    pass

class Containers(object):
    """
    Operations on the set of containers which pertain to dvol.  Also maintain
    state on which containers we stopped so that we can start them again.

    @ivar stopped: mapping from volume name for which we stopped containers to
        set of container ids, so that we can attempt to start them again.
    """
    def __init__(self):
        self.stopped = dict()
        self.c = docker.client.Client()

    def stop(self, volume):
        pass

    def start(self, volume):
        if volume not in self.stopped:
            raise NeverLocked("never locked %s, can't unlock it" % (volume,))
        for cid in self.stopped[volume]:
            try:
                self.c.start(cid)
            except:
                log.err(None, "while trying to start %s" % (cid,))
        del self.stopped[volume]

