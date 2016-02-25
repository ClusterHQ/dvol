#!/bin/bash
set -e

echo "running tests..."
gotestcover -race -covermode=count -coverprofile=cover.out $(go list ./... | grep -v /vendor/)

echo ""
go tool cover -func cover.out
