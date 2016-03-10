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

  # We need to remove the existing version as we cannot add --force-confnew
  # to the apt-get install in the following call
  sudo apt-get --force-yes -y -q remove docker-engine

  # Remove the config file
  sudo rm /etc/default/docker

  # Install the 'experimental' build from Docker
  curl -sSL https://experimental.docker.com/ | sudo sh
else
  # 'upgrade' docker-engine to specific version
  sudo apt-get -o Dpkg::Options::="--force-confnew" install -y --force-yes docker-engine=${DOCKER_VERSION}-0~trusty
fi
