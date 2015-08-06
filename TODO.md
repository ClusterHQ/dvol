# todo

* fix reset-while-running-container bug? test with pause/unpause?
    * two possible fixes:
        1. stop container and then start it again (we need to be able to do this anyway for snapshots, I think).
           disadvantage: interactive sessions will get killed. it won't be possible to save interactive sessions anyway, if the mount-point needs to change directory inode (I think).
        2. scrape out the contents of the volume but don't delete the directory.
           not sure if this will work with zfs backend (I suspect it would work for rollbacks, but maybe not switching branches, which won't work with file based backend either).
      going with #1...
* know and show which containers are using a volume right now (augment list output)

---

* demo making test runs faster

---

* demo with (visually) inserting data into database and rolling back

---

* seeing what branch you're on and what branches there are (dvol branch)
* branching from a commit (dvol branch master boozer)
* switching to a branch (dvol checkout boozer)
* branch and switch in one go (dvol checkout -b newbranch)

---

* demo with kai's moby counter app (switching branches)

---

* push and pull between hosts/users (rsync/scp to begin with)

---

* zfs backend
* make slow backend operations recommend trying the zfs backend

---

* give commit an option to do a snapshot without stopping the container first

(the following should be features of flocker, really.)

* auto-commit (supporting above action)
* auto-push

---

* container quiesce hooks (ftwrl etc)
* support HEAD^ syntax?

---

* auto-commit on container stop/start?

* show stopped/running containers with cute unicode [] and |> symbols.

# done

* listing volumes (dvol list)

* should commits be an attribute of volumes or of branches?
    * maybe they should float as top-level things but our branches should record a list of them?
    * let's see how this goes with the file-based and zfs-based backends; notably zfs *won't* be this shape

* listing commits (dvol log)

* rolling back to commits (dvol reset --hard {HEAD,commit})

* docker integration via volume plugin
