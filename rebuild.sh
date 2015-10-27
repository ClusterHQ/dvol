#!/bin/sh
docker build -t clusterhq/dvol .
docker restart dvol-docker-plugin
