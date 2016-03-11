#!/bin/sh
set -xe
rm -rf output
mkdir output
docker build -t clusterhq/static-cp .
docker run -v ${PWD}/output:/output clusterhq/static-cp cp /target/cp /output/
