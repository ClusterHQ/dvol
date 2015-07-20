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
