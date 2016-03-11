#!/bin/sh

# Installs either a known version of Docker or the 'experimental' build.
#
# Usage example:
#
# $ scripts/build-travis-install-docker.sh 1.10.2
# or
# $ scripts/build-travis-install-docker.sh experimental

set -xe

# Exit early if no parameters set
if [ $# -eq 0 ]; then
  exit 0
fi

DOCKER_VERSION=$1

if [ $DOCKER_VERSION = "experimental" ]; then

  # install the 'experimental' version
  apt_url="https://apt.dockerproject.org"
  lsb_dist="ubuntu"
  dist_version="trusty"
  repo="experimental"
  gpg_fingerprint="58118E89F3A912897C070ADBF76221572C52609D"

  sudo apt-key adv -k ${gpg_fingerprint} >/dev/null
  sudo mkdir -p /etc/apt/sources.list.d

  sudo su -c "echo deb [arch=$(dpkg --print-architecture)] ${apt_url}/repo ${lsb_dist}-${dist_version} ${repo} > /etc/apt/sources.list.d/docker.list"

  sudo cat /etc/apt/sources.list.d/docker.list

  sudo apt-get update;
  sudo apt-get -o Dpkg::Options::="--force-confnew" install -y --force-yes -q docker-engine


else
  # 'upgrade' docker-engine to specific version
  sudo apt-get -o Dpkg::Options::="--force-confnew" install -y --force-yes docker-engine=${DOCKER_VERSION}-0~trusty
fi

docker version
