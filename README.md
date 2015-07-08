# dvol: voluminous for Docker
## It's like Git for your development database's Docker volumes.

Key observation: doing interesting things with data volumes involves traversing
a tree structure. What tree structure are developers everywhere familiar with
traversing? Answer: Git.

Therefore: model an interesting local developer data volume tool on git.

## Model
 * **volume**: a base version of some data... like a git repo... defaults to a
   master branch
 * **branch**: a "zfs clone" of a snapshot of a filesystem (branching
   require a commit, uses the most recent commit)
 * **commit**: a "zfs snapshot" - with a uuid and a commit message stored in
   metadata
     - unlike with git, commits can be deleted (cleaned up) to clear space
 * **diff**: compare the difference between two commits (in the same tree)

Could be extended to support btrfs as well.

In the future, push/pull will work to volume hub, and/or Flocker cluster in
production.

## UI metaphors to copy
 * docker-style listings of e.g. top-level volumes
 * git-style branch and commit semantics (where it makes sense)

## Design decisions
 * Volumes don't manifest on the host, if you want to get "at" one, you run a
   container with it mounted. (This eases boot2docker integration).
 * Therefore, which directory you're in doesn't affect which volume you're
   handling.

Provides CLI from which volumes (usable in volume driver) can be snapshotted,
cloned.

Should be doable entirely in terms of ZFS commands.

# Sample shell transcript

```
$ cd /Projects
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
  volume_driver: flocker

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
