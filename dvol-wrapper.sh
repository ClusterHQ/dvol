#!/bin/sh
docker run --rm -ti --volumes-from dvol-volumes \
    -v /run/docker/plugins:/run/docker/plugins \
    -v /var/run/docker.sock:/var/run/docker.sock \
    clusterhq/dvol dvol $@
