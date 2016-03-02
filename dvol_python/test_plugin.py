"""
log of integration tests to write:

write test_switch_branches_restarts_containers

command:
    docker-compose up -d (in a directory with appropriate docker-compose.yml file)
expected behaviour:
    docker containers are started with dvol accordingly

command:
    docker run -ti --volume-driver dvol -v hello:/data busybox sh
expected output:
    dvol volume is created on-demand

command:
    dvol commit ...
expected behaviour:
    a container which only persists its in-memory state to disk occasionally (e.g. on shutdown) has correctly written out its state

command:
    dvol reset...
expected behaviour:
    a container which caches disk state in memory has correctly updated its state (IOW, containers get restarted around rollbacks)

command:
    run a container using a dvol volume
expected behaviour:
    dvol list
    container names shows up in output
"""
