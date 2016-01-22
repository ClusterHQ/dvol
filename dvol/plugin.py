"""
Docker Voluminous plugin from ClusterHQ
Runs on boot, provides plugin to docker via
https://github.com/docker/docker/blob/master/experimental/plugin_api.md

Enables:

    $ docker run --volume-driver=dvol -v volume:/foo postgresql

(or the equivalent in docker compose, which is targeted at development
environments)

"volume" object can be a volume @ master, or a branch (clone) of a snapshot of
a volume...

"""

from twisted.application import internet
from twisted.internet import reactor
from twisted.web import server, resource
from twisted.python.filepath import FilePath
import json
from dvol import Voluminous, VOLUME_DRIVER_NAME

# Return value to docker for no Error.
_NO_ERROR = ""

class HandshakeResource(resource.Resource):
    """
    A hook for initial handshake.  Say that we're a volume plugin.
    """
    isLeaf = True

    def __init__(self, voluminous):
        self.voluminous = voluminous
        resource.Resource.__init__(self)

    def render_POST(self, request):
        print "done handshake"
        return json.dumps(dict(
             Implements=["VolumeDriver"],
        ))

class CreateResource(resource.Resource):
    """
    Docker has asked us to create a named volume.

    Create the volume on-demand.
    """
    isLeaf = True

    def __init__(self, voluminous):
        self.voluminous = voluminous
        resource.Resource.__init__(self)

    def render_POST(self, request):
        payload = json.loads(request.content.read())
        print "create:", payload
        try:
            if not self.voluminous.exists(payload["Name"]):
                self.voluminous.createVolume(payload["Name"])
            return json.dumps(dict(
                 Err=_NO_ERROR,
            ))
        except Exception, e:
            return json.dumps(dict(
                err=("voluminous '%(name)s' creation failed: %(err)s" %
                    dict(name=payload["name"], err=str(e))
            )))

class RemoveResource(resource.Resource):
    """
    Docker has asked us to remove a named volume.  In our case, we disregard
    this request, because flocker volumes are supposed to be able to outlive
    docker volumes.
    """
    isLeaf = True

    def __init__(self, voluminous):
        self.voluminous = voluminous
        resource.Resource.__init__(self)

    def render_POST(self, request):
        # expect Name
        payload = json.loads(request.content.read())
        print "remove:", payload
        return json.dumps(dict(
             Err=_NO_ERROR,
        ))

class PathResource(resource.Resource):
    """
    Docker has asked us for the concrete on-disk location of an volume. Create
    it on demand.
    """
    isLeaf = True

    def __init__(self, voluminous):
        self.voluminous = voluminous
        resource.Resource.__init__(self)

    def render_POST(self, request):
        payload = json.loads(request.content.read())
        print "path:", payload
        path = None
        return json.dumps(dict(
             Mountpoint=path,
             Err=_NO_ERROR,
        ))

class UnmountResource(resource.Resource):
    """
    Docker has asked us to unmount a volume.  Rather, it has notified us that
    it is no longer actively using a container with this volume.
    """
    isLeaf = True

    def __init__(self, voluminous):
        self.voluminous = voluminous
        resource.Resource.__init__(self)

    def render_POST(self, request):
        # expect Name
        payload = json.loads(request.content.read())
        print "unmount:", payload
        # XXX actually 'release' the volume in some sense
        return json.dumps(dict(
             Err=_NO_ERROR,
        ))

class MountResource(resource.Resource):
    """
    A hook for container start.
    """
    isLeaf = True

    def __init__(self, voluminous):
        self.voluminous = voluminous
        resource.Resource.__init__(self)

    def render_POST(self, request):
        payload = json.loads(request.content.read())
        print "mount:", payload
        if self.voluminous.exists(payload["Name"]):
            # TODO - (asynchronously?) add this container id to the set of
            # active containers to show up in the dvol list output?
            return json.dumps(dict(
                Mountpoint=self.voluminous.updateRunningPoint(payload["Name"]),
                Err=_NO_ERROR,
            ))
        else:
            return json.dumps(dict(
                Mountpoint="",
                Err=("Voluminous '%(name)s' does not exist, "
                     "create it with: dvol init %(name)s" % (dict(name=payload["Name"]))),
            ))

        new_json = {}
        path = None
        if path:
            new_json["Mountpoint"] = path
            new_json["Err"] = _NO_ERROR
        else:
            # This is how you indicate not handling this request
            new_json["Mountpoint"] = ""
            new_json["Err"] = "unable to handle"
        return json.dumps(new_json)


def getAdapter(voluminous):
    root = resource.Resource()
    root.putChild("Plugin.Activate", HandshakeResource(voluminous))
    root.putChild("VolumeDriver.Create", CreateResource(voluminous))
    root.putChild("VolumeDriver.Remove", RemoveResource(voluminous))
    root.putChild("VolumeDriver.Path", PathResource(voluminous))
    root.putChild("VolumeDriver.Mount", MountResource(voluminous))
    root.putChild("VolumeDriver.Unmount", UnmountResource(voluminous))

    site = server.Site(root)
    return site


def main():
    plugins_dir = FilePath("/run/docker/plugins/")
    if not plugins_dir.exists():
        plugins_dir.makedirs()

    dvol_path = FilePath("/var/lib/dvol/volumes")
    if not dvol_path.exists():
        dvol_path.makedirs()
    voluminous = Voluminous(dvol_path.path)

    sock = plugins_dir.child("%s.sock" % (VOLUME_DRIVER_NAME,))
    if sock.exists():
        sock.remove()

    adapterServer = internet.UNIXServer(
            sock.path, getAdapter(voluminous))
    reactor.callWhenRunning(adapterServer.startService)
    reactor.run()
