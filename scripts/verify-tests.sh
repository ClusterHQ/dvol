#!/bin/bash
set -e

# run test coverage on each subdirectories and merge the coverage profile.
echo "running go test..."
echo "mode: count" > profile.cov

# standard go tooling behavior is to ignore dirs with
# leading underscores and the vendored dependencies
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

