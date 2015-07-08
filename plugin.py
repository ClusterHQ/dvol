"""
Voluminous docker plugins.
Runs on boot, provides plugin to docker via
https://github.com/docker/docker/blob/master/experimental/plugin_api.md

Also provides API for client to talk to... for snapshotting, cloning, rolling
back things.

Enables:

    $ docker run --volume-driver=voluminous -v volume:/foo postgresql

(or the equivalent in docker compose, which is targeted at development
environments)

"volume" object can be a volume @ master, or a branch (clone) of a snapshot of
a volume...
"""
