# todo

* grab email & name from ~/.gitconfig, add date too

* demo making test runs faster

# done

* listing volumes (dvol list)

* should commits be an attribute of volumes or of branches?
    * maybe they should float as top-level things but our branches should record a list of them?
    * let's see how this goes with the file-based and zfs-based backends; notably zfs *won't* be this shape

* listing commits (dvol log)

* rolling back to commits (dvol reset --hard {HEAD,commit})

* docker integration via volume plugin

* know and show which containers are using a volume right now (augment list output)

* fix reset-while-running-container bug? test with pause/unpause?
    * two possible fixes:
        1. stop container and then start it again (we need to be able to do this anyway for snapshots, I think).
           disadvantage: interactive sessions will get killed. it won't be possible to save interactive sessions anyway, if the mount-point needs to change directory inode (I think).
        2. scrape out the contents of the volume but don't delete the directory.
           not sure if this will work with zfs backend (I suspect it would work for rollbacks, but maybe not switching branches, which won't work with file based backend either).
      going with #1...

---

* dockerize dvol
    * it could bootstrap on bind-mounts (/var/run/docker.sock, /var/lib/dvol)
    * dvol docker plugin becomes restart=always container
    * dvol command itself becomes shell script wrapper around docker run

* support HEAD^ syntax

* fix bug where resetting doesn't delete newer commit references

* seeing what branch you're on and what branches there are (dvol branch)
* switching to a branch (dvol checkout newbranch)
* branch and switch in one go (dvol checkout -b newbranch)
* branching from the head of a branch (dvol checkout master; dvol checkout -b newbranch)
* delete a branch (dvol branch -d newbranch)

* are you sure

* make a call on uncommitted changes on branches (UX would be easier if we could see how big they were)

* recording current volume, stop requiring <volume> on every command, add 'dvol switch' command

* dvol list branch output

---

* demo with (visually) inserting data into database and rolling back
* demo with kai's moby counter app (switching branches)

* fix commit messages with spaces in them

---

* delete volumes
