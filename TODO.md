* listing volumes (dvol list)
* listing commits (dvol log)
* rolling back to commits (dvol reset --hard {HEAD,commit})

---

* docker integration via volume plugin
* show which containers are using a volume right now (augment list output)

---

* demo with inserting data into database

---

* seeing what branch you're on and what branches there are (dvol branch)
* branching from a commit (dvol branch master boozer)
* switching to a branch (dvol checkout boozer)
* branch and switch in one go (dvol checkout -b newbranch)

---

* demo with kai's moby counter app (switching branches)

---

* push and pull between hosts/users (scp to begin with)

---

* zfs backend
* make slow backend operations recommend trying the zfs backend

---

* give commit an option to do a snapshot without stopping the container first
* auto-commit (supporting above action)
* auto-push

---

* container quiesce hooks
