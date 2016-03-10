#!/bin/sh

# Installs either a known version of Docker or the 'experimental' build.

set -xe

# exit if DOCKER_VERSION is not set
if [ -z "$DOCKER_VERSION" ]; then
  exit 0
fi

if [ $DOCKER_VERSION = "experimental" ]; then
  # 'upgrade' docker-engine to specific version
  sudo apt-get -o Dpkg::Options::="--force-confnew" install -y --force-yes docker-engine=${DOCKER_VERSION}-0~trusty
else
  # install the 'experimental' build from Docker
  sudo sh -c 'curl -sSL https://experimental.docker.com/'
fi
