#!/bin/sh
docker run -ti -v /run/docker/plugins:/run/docker/plugins -v /var/run/docker.sock:/var/run/docker.sock dvol-docker-plugin dvol $@
