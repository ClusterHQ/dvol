#!/bin/sh
set -e
PROJECT=$1
CMD_PATH=$2
TAG=$3

mkdir -p ${PROJECT}-build
# XXX Need to make sure this is go 1.5.
CGO_ENABLED=0 GOOS=linux godep go build -a -ldflags '-s' ${CMD_PATH}
mv ${PROJECT} ${PROJECT}-build/
cp Dockerfile.${PROJECT} ${PROJECT}-build/Dockerfile
cd ${PROJECT}-build && docker build -t clusterhq/${PROJECT}:${TAG} .
rm -rf ${PROJECT}-build/
