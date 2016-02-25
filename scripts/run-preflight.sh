#!/bin/bash
set -e

# automatic checks
echo "running gofmt..."
test -z "$(gofmt -l -w .     | tee /dev/stderr)"

echo "running goimports..."
test -z "$(goimports -w .    | tee /dev/stderr)"

echo "running go vet..."
godep go vet ./...

# run test coverage on each subdirectories and merge the coverage profile.
echo "running go test..."
 
echo "mode: count" > profile.cov 
# standard go tooling behavior is to ignore dirs with leading underscors
for dir in $(find . -maxdepth 10 -not -path './.git*' -not -path '*/vendor/*' -not -path '*/_*' -type d);
do
if ls $dir/*.go &> /dev/null; then
    godep go test -race -covermode=count -coverprofile=$dir/profile.tmp $dir
    if [ -f $dir/profile.tmp ] 
    then
        cat $dir/profile.tmp | tail -n +2 >> profile.cov
        rm $dir/profile.tmp
    fi
fi
done

go tool cover -func profile.cov