#!/bin/sh

# Installs either a known version of Docker or the 'experimental' build.
# Usage example:
#
# $ scripts/build-install-docker.sh 1.10.2
# or
# $ scripts/build-install-docker.sh experimental

set -xe

# Exit early if a 'Docker Version' is not set
if [ $# -eq 0 ]; then
  exit 0
fi

DOCKER_VERSION=$1

if [ $DOCKER_VERSION = "experimental" ]; then

  # We need to remove the existing installation
  sudo apt-get --force-yes -y -q remove docker-engine

  sudo wget https://experimental.docker.com/builds/Linux/x86_64/docker-latest -O /usr/bin/docker

  sudo chmod +x /usr/bin/docker

  sudo /usr/bin/docker daemon &

else
  # 'upgrade' docker-engine to specific version
  sudo apt-get -o Dpkg::Options::="--force-confnew" install -y --force-yes docker-engine=${DOCKER_VERSION}-0~trusty
fi

docker version
