"""
log of integration tests to write:

command:
    docker run -ti --volume-driver dvol -v hello:/data busybox sh
expected output:
    Error response from daemon: Voluminous 'hello2' does not exist, create it with: dvol init hello2

command:
    sudo dvol init hello2
expected output:
    Created volume hello2
    Created branch hello2/master

command:
    sudo dvol commit ...
expected behaviour:
    a container which only persists its in-memory state to disk occasionally (e.g. on shutdown) has correctly written out its state

command:
    sudo dvol rollback ...
expected behaviour:
    a container which caches disk state in memory has correctly updated its state (IOW, containers get restarted around rollbacks)

command:
    run a container using a dvol volume
    sudo dvol list
    container names shows up in output
"""
