#!/bin/bash
set -e

# automatic checks
test -z "$(gofmt -l -w .     | tee /dev/stderr)"
test -z "$(goimports -w .    | tee /dev/stderr)"
go vet ./...
go test -race ./...

# run test coverage on each subdirectories and merge the coverage profile. 
echo "mode: count" > profile.cov
 
# standard go tooling behavior is to ignore dirs with leading underscors
for dir in $(find . -maxdepth 10 -not -path './.git*' -not -path '*/_*' -type d);
do
if ls $dir/*.go &> /dev/null; then
    godep go test -covermode=count -coverprofile=$dir/profile.tmp $dir
    if [ -f $dir/profile.tmp ] 
    then
        cat $dir/profile.tmp | tail -n +2 >> profile.cov
        rm $dir/profile.tmp
    fi
fi
done

go tool cover -func profile.cov