#!/bin/sh

# Build a "FROM scratch" docker image based on some
# statically compiled binaries. Usage example:
#
# $ scripts/build-golang-docker-image.sh \
#   	--project "dvol" \
#   	--source-files "dvol.go cmd/dvol-docker-plugin/dvol-docker-plugin.go" \
#   	--binaries "dvol dvol-docker-plugin" \
#   	--tag "golang"
#
# XXX: Currently you have to specify the arguments in exactly this order.
# TODO: Make this actually do proper argument parsing.

set -xe

export GO15VENDOREXPERIMENT=1

PROJECT=$2
SOURCE_FILES=$4
BINARIES=$6
TAG=$8

# Statically compile the binaries
for SOURCE_FILE in $SOURCE_FILES; do
    # XXX Need to make sure this is go 1.5 to avoid bug in
    # older versions of docker.
    CGO_ENABLED=1 GOOS=linux godep go build -a -ldflags '-s' ${SOURCE_FILE}
done

mkdir -p ${PROJECT}-build
# Copy them into the build directory
for BINARY in $BINARIES; do
    cp ${BINARY} ${PROJECT}-build/
done

# Copy the dockerfile
cp Dockerfile.${PROJECT} ${PROJECT}-build/Dockerfile

# Build the docker image in a constrained context.
cd ${PROJECT}-build
docker build -t clusterhq/${PROJECT}:${TAG} .
cd ..

# Clean up
rm -rf ${PROJECT}-build/
