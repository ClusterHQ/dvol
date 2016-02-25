#!/bin/bash
set -e

echo "running goimports..."
test -z "$(goimports -w .    | tee /dev/stderr)"

echo "running gofmt..."
test -z "$(gofmt -l -w .     | tee /dev/stderr)"

echo "running go vet..."
godep go vet ./...
