# dvol: version control for your development databases in docker

Key observation: doing interesting things with data volumes involves traversing
a tree structure. What tree structure are developers everywhere familiar with
traversing? Answer: Git.

Therefore: model an interesting local developer data volume tool on git.

dvol walkthrough (2 minutes)

[![dvol clusterhq](http://img.youtube.com/vi/aXMNp-L_-1c/0.jpg)](https://youtu.be/aXMNp-L_-1c)

## Model
 * **volume**: a base version of some data... like a git repo... defaults to a
   master branch
 * **branch**: a "clone" of a snapshot of a filesystem (branching
   require a commit, uses the most recent commit)
 * **commit**: a "snapshot" - with a uuid and a commit message stored in
   metadata
     - unlike with git, commits can be deleted (cleaned up) to clear space
 * **diff**: compare the difference between two commits (in the same tree)

Commit and rollback require atomic filesystem snapshots. In the first
iteration, we'll support this by just stopping containers using a volume before
committing/rolling back.

Could be extended to support zfs and btrfs as well, and then filesystem
snapshots can be atomic and much more efficient.

In the future, push/pull will work to volume hub, and/or Flocker cluster in
production.

## UI metaphors to copy
 * docker-style listings of e.g. top-level volumes
 * git-style branch and commit semantics (where it makes sense)

## Design decisions
 * Volumes don't manifest on the host, if you want to get "at" one, you run a
   container with it mounted. (This eases boot2docker integration).
 * Alternative: (do not require docker) allow volumes to manifest on the host,
   just as symlinks: "dvol expose".
 * Nevertheless, which directory you're in doesn't affect which volume you're
   handling.

Provides CLI from which volumes (usable in volume driver) can be snapshotted,
cloned.

# Sample shell transcript

```
$ cd ~/Projects
$ ls
HybridCP TweetDeckMonitor MediaGenius

# HybridCP is a php + mysql app
# TweetDeckMonitor is a JS + twisted + redis server monitoring app
# MediaGenius is a php + elasticsearch app
# (these are all real apps from my development past)

$ dvol init HybridCP/mysql
Created empty volume HybridCP/mysql.

$ docker-compose up -d

$ dvol list
VOLUME                     SIZE     BRANCHES
HybridCP/mysql             0.32G    1
TweetDeckMonitor/redis     6.72G    3
MediaGenius/elasticsearch  1.23G    2

$ cd HybridCP

$ cat docker-compose.yml
web:
  image: lmarsden/app:testbranch
  links: [db]
  volumes:
    - /home/luke/app:/app
db:
  image: postgresql
  volumes:
    - HybridCP/mysql:/var/lib/mysql
  volume_driver: dvol

$ docker-compose up -d
$ docker-compose ps
    Name           Command                    State       Ports
-------------------------------------------------------------------
hybridcp_mysql_1   /usr/local/bin/mysqld      Up
hybridcp_web_1     /bin/sh -c python app.py   Up      5000->5000/tcp

$ docker exec -ti hybridcp_mysql_1 mysql < schemas/base-schema.sql
$ dvol commit -m "import base schema" HybridCP/mysql

$ dvol log
commit fd39db24343ed426fc3fcbcf11a201d996d18429
Author: Luke Marsden <luke@clusterhq.com>
Date:   Wed Jul 8 15:00:05 2015 +0100

    import base schema

$ dvol diff
200Kb has changed between "import base schema" and latest uncommitted
changes.  Use dvol diff -v to show changed files.

$ dvol checkout -b schema-tweaks
Volume HybridCP/mysql has uncommitted changes. Please commit these before
switching branches.

$ dvol reset --hard HEAD HybridCP/mysql
Container hybridcp_mysql_1 is using HybridCP/mysql, please stop it before
resetting.

$ docker-compose rm -f
$ dvol reset --hard HEAD HybridCP/mysql
Resetting HybridCP/mysql to latest commit... done.

$ dvol checkout -b schema-tweaks
Switched to branch schema-tweaks based from HybridCP/mysql master@HEAD.

$ docker-compose up -d
$ docker run -ti --volume-driver=dvol HybridCP/mysql mysql
mysql> alter table users add index blah;
mysql> ^D

$ dvol log
commit 95c1c55093a9b8e3188dba6147115da741803389
Author: Luke Marsden <luke@clusterhq.com>
Date:   Wed Jul 8 15:27:35 2015 +0100

    experiment with adding indexes to users table

commit fd39db24343ed426fc3fcbcf11a201d996d18429
Author: Luke Marsden <luke@clusterhq.com>
Date:   Wed Jul 8 15:00:05 2015 +0100

    import base schema

$ docker-compose rm -f
$ dvol checkout master HybridCP/mysql
$ dvol log
commit fd39db24343ed426fc3fcbcf11a201d996d18429
Author: Luke Marsden <luke@clusterhq.com>
Date:   Wed Jul 8 15:00:05 2015 +0100

    import base schema

$ docker-compose up -d # now the app is running with the master version of the
                       # data, before the indexes were added
```


## ideas? feedback? issues? bugs?
We absolutely really appreciate your ideas, feature request, pulls, and issues/bug reports for dvol, because we believe in building useful and user friendly tools for our communities.
also feel free to send us a email at <feedback@clusterhq.com>
