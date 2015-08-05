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

"""
