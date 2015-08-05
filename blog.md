# Docker Voluminous plugin from ClusterHQ

At ClusterHQ we started out making stateful containers work in production with Flocker.

We are also interested in how stateful containers can be useful for developers in development environments.

So we asked ourselves the question: what do developers spend most of their time doing?

Two things came to the top of the list: waiting for tests, and tracking down and reproducing bugs.

## What is voluminous?

Voluminous is a developer tool which brings git-like functionality to Docker volumes.
This means you can commit, reset and (coming soon: branch) Voluminous Docker volumes.

## Why is voluminous useful?

We've thought of two reasons so far.
If you come up with others, let us know!

### Speeding up tests

You can speed up integration tests by caching database state as a commit, and rolling back to it rather than re-creating your database from scratch every time you run the tests.

### Interactive debugging

Found a bug in your app which only manifests when the database is in a certain state?
Commit the database state and save it, along with the code state, for later debugging.
It's like having bookmarks for your development database.

(Coming soon: share your voluminous volumes with colleagues using `dvol push` and `pull`, maintain a catalog of sample data).

## How do I use voluminous?

Voluminous volumes, like Docker containers, are global to your development machine.

You manage Voluminous with a command line tool called `dvol`:

```
$ dvol --help
Usage: dvol [options]
Commands:
    list    List all volumes
    init    Create a volume and its default master branch
    commit  Create a commit on a branch
    log     List commits on a branch
    reset   Reset a branch to a given commit, throwing away more recent data
$ dvol init frob_mysql
```

You can start Docker containers with Voluminous volumes:

```
$ docker run -v frob_mysql:/data --volume-driver=dvol busybox sh -c "echo hello > /data/file"
```

Now make a commit:

```
$ dvol commit -m "Hello" frob_mysql
```

Now overwrite the file:

```
$ docker run -v frob_mysql:/data --volume-driver=dvol busybox sh -c "echo world > /data/file"
$ docker run -v frob_mysql:/data --volume-driver=dvol busybox cat /data/file
world
```

If you need your volume state back, reset it:

```
$ dvol reset --hard HEAD frob_mysql
$ docker run -v frob_mysql:/data --volume-driver=dvol busybox cat /data/file
hello
```

## That's a neat trick, but how is it useful when I'm developing an app?

## Reference: semantics

* Volumes have a non-empty set of branches.
* Branches have initially-empty ordered list of commits.
* Commits have metadata: commit message, author, date.

* You can create a commit from the current state of a branch with `dvol commit`.
* You can create a new branch from the tip commit of a the current branch with `dvol checkout -b <branchname>`.

    * Unlike `git`, creating a new branch in this way will not carry across uncommitted changes.

## Reference: implementation

Voluminous volumes, with the default plain filesystem driver, consist of a branches, which is a directory of files in `/var/lib/dvol/volumes/<volumename>/branches/<branchname>`, and a set of commits in `/var/lib/dvol/volumes/<volumename>/commits/<id>`, which are simply copies of those directories.

