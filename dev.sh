#!/bin/bash
docker create \
       -it \
       --name dvol-development \
       --volume ${PWD}:/golang/src/github.com/ClusterHQ/dvol \
       # Expose the host Docker inside the container. This means we still have
       # global (docker) state inside the containers. Probably okay for now.
       # Later, switch to real docker-in-docker configuration for better
       # isolation.
       --volume /var/run/docker.sock:/var/run/docker.sock \
       --workdir /golang/src/github.com/ClusterHQ/dvol \
       clusterhq-dev/dvol
docker start -ia dvol-development
