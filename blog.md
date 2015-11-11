# Making the (bridging the gap/making the leap/easing the transition) development to production
# ALT: The Path to Docker in Production
# ALT: dvol: Paving the road to Docker in Production
# ALT: dvol: developers, developers, developers!

At ClusterHQ we are laser focused on making stateful containers a reality for developers and teams ready to make the jump into production.

Before making the jump to production with stateful containers Developers should first have confidence in the tools they are testing in their development and testing environments. To help ease the stress of making this leap our team has been in the labs working on a set of tools that will help increase confidence and reduce the cycle of waiting for test and debugging failures.

We had some clear goals with this tool
- makes it faster to develop with docker
- improve the development user experience

## Introducing dvol  

Dvol is a cli tool that brings git-like functionality the universe of Docker volumes.
It brings familiar features such as the ability to commit, branch, diff, and roll back volumes.

## Why is it useful to treat volumes with a git like interface?


## 1. Speeding up tests
`dvol commit -m “updated product table for march`

Problem: A full restore from a large (30Gb) dbdump file can take several hours.

With the `dvol commit` developers can now version and commit the state of their database. You could simply cache your database state and rollback quickly to a earlier state programmatically.

## 2. Interactive debugging
`dvol commit -m “index of product_id with updated db 10.4 breaks tests`

Found a bug in your app which only manifests when the database is in a certain state?
Commit the database state and save it, along with the code state, for later debugging.
It's like having bookmarks for your development database.

## 3. Future work and Ideas: Push, Pull, and Clone
`dvol push/pull/clone <volume>`

1 and 2 are great for a single developer on a local machine. As we validate this workflow we believe that real “oh wow” moments will come from being able to push and pull your volume from a shared resource preventing the need for your team create and manage a system for versioning and sharing increasingly large sql files and backups.

Being able to push/pull trusted data from a catalog will enable teams of all formations to worry about how to share and organize these files.



## How do I install it?

requirements: Docker 1.8.1+
You can also use a tiny wrapper script to make it easier to run the client binary.

On Linux or OSX , run the following commands:

#### 1. start the dvol docker tool via `docker run`
`docker run -v /var/lib/dvol:/var/lib/dvol --restart=always -d \
    -v /run/docker/plugins:/run/docker/plugins \
    -v /var/run/docker.sock:/var/run/docker.sock \
    --name=dvol-docker-plugin clusterhq/dvol`

#### 2. Create a local shell script wrapper to run dvol
```
cat > dvol <<EOF
#!/bin/sh
docker run --rm -ti -v /var/lib/dvol:/var/lib/dvol \\
    -v /run/docker/plugins:/run/docker/plugins \\
    -v /var/run/docker.sock:/var/run/docker.sock \\
    clusterhq/dvol dvol \$@
EOF
```
#### 3. Install it
```
sudo mv dvol /usr/local/bin/dvol
sudo chmod +x /usr/local/bin/dvol
```
#### 4. Have A Nice Day.
```
dvol --help
Usage: dvol [options]
Options:
  -p, --pool=    The name of the directory to use
      --version  Display Twisted version and exit.
      --help     Display this help and exit.
Commands:
    list          List all voluminous volumes
    ls            Same as 'list'
    init          Create a volume and its default master branch, then switch to
                  it
    switch        Switch active volume for commands below (commit, log etc)
    rm            Destroy a voluminous volume
    commit        Create a commit on the active volume and branch
    log           List commits on the active volume and branch
    reset         Reset active branch to a commit, destroying later unreferenced
                  commits
    branch        List or delete branches for active volume
    checkout      Check out or create branches on the active volume
```

## How do I use it?

- *dvol CLI* : primary user interface for dvol, init, commit, reset, branch, etc.
- *dvol Docker*: Volume Plugin* quickly connect your containers to your dvol volumes. `--volume-driver=dvol`
- *dvol volumes*: like Docker containers, are global to your development machine.

#### 1. init a new volume
$ `dvol init frob_mysql`

You can start your docker containers with the `—volume-driver=dvol` command, take notice how we are mounting our volume within the frob_mysql directory with `frob_mysql:/data`

```
#### 2. creating data
```
$ docker run -v frob_mysql:/data --volume-driver=dvol busybox sh -c "echo hello > /data/file"
```
#### 3. commit the changes
use the `-m` flag to include a message with your commit
```
$ dvol commit -m “added ‘hello’ to the volume“ frob_mysql
```

#### 3. Change the file
Lets overwrite the “hello” we placed into frob_mysql:/data/file with the word “world”
```
$ docker run -v frob_mysql:/data --volume-driver=dvol busybox sh -c "echo world > /data/file"
```

#### 3. reset back to the first commit
Notice how we haven’t committed our changed frob_mysql:/data/file with the newly overwritten “world” text? Let’s reset our volume and bring it back to the state when we made our first commit, “hello”. 
```
$ dvol reset --hard HEAD frob_mysql
$ docker run -v frob_mysql:/data --volume-driver=dvol busybox cat /data/file
hello
```

## Why wouldn’t you… 
Let us attempt to quickly identify some of the current solutions and problems where they fall short for developers.
### 1. *name files as a form of versioning* 
Trying to intelligent name files is complex and prone to error and requires clear protocol across development teams. A developer might find him self with numerous crazy naming schemes over the course of their career.
### 2. *I have this thumbdrive…*
thumbdrives are great if your team is within the same building. They also have limitations of space require human time to keep track of manage, and transfer them around. Passing around a thumb drive of even the best scrubbed user database can be a security team’s worst nightmare. “opps! I lost that drive with our entire product catalog on it sometime last week”
### 3. *use Dropbox, Google Drive, S3, Azure*
Dropbop, Google Drive, S3 were not meant to treat large files in a developer first manner. Do you want to sync all your files all the time? what about that minor change that effected that 30gb file in a directory of numerous files? That is not to say that these commodity services won’t ultimately be pluggable backends to push, pull, and clone from.
### 3. *Github’s Large File Store*
directly from github [documentation](https://help.github.com/articles/what-is-my-disk-quota/):
> We recommend repositories be kept under 1GB each. This limit is easy to stay within if large files are kept out of the repository. If your repository exceeds 1GB, you might receive a polite email from GitHub Support requesting that you reduce the size of the repository to bring it back down.
> We place a strict limit of files exceeding 100 MB in size
> Large SQL files do not play well with version control systems such as Git. If you are looking to provide your developers with the most recent production dataset, we recommend using Dropbox for sharing files like these among your developers.

### 2. *why not email, IRC, Slack the files around in a adhoc manner*

sigh.

## Does the community really need this?
This tool is open source and we looking for feedback from the community. Email us at [mailto:feedback@clusterhq.com](feedback@clusterhq.com).
We have a [meetup](http://www.meetup.com/ClusterHQ-SF/events/226500685/) at our San Francisco office on November 11th 2015 to discuss the solution and it’s implications. 

## That's a neat trick, but how is it useful when I'm developing an app?

TODO

## Reference: semantics

* Volumes have a non-empty set of branches.
* Branches have initially-empty ordered list of commits.
* Commits have metadata: commit message, author, date.
* You can create a commit from the current state of a branch with `dvol commit`.
* You can create a new branch from the tip commit of a the current branch with `dvol checkout -b <branchname>`.

    * Unlike `git`, creating a new branch in this way will not carry across uncommitted changes.
* You can reset to a commit on a current branch, which throws away newer commits and uncommitted changes.
    * This restarts any containers using the volume so that they reload the state on disk.
* You can switch branches so long as you have no uncommitted changes.
    * This restarts any containers using the volume so that they reload the state on disk.

## Reference: implementation

dvol volumes, with the default plain filesystem driver, consist of a branches, which is a directory of files in `/var/lib/dvol/volumes/<volumename>/branches/<branchname>`, and a set of commits in `/var/lib/dvol/volumes/<volumename>/commits/<id>`, which are simply copies of those directories.

Commit metadata is stored in json files in the branches directory.
