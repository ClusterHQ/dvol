# Version control for your development databases in Docker

`dvol` lets you `commit`, `reset` and `branch` the containerized databases running on your laptop so you can easily save a particular state and come back to it later.

# Installation

## Step 1

[Install Docker](https://docs.docker.com/) 1.8.0 or later.

## Step 2

```
$ curl -sSL https://get.dvol.io |sh
```

This will pull the `dvol` docker image, run the `dvol` docker volume plugin, and set up a tiny wrapper script in `/usr/local/bin/dvol`.

# Data model

* **Volume**: a named repository for data files (e.g. database data files) which can be mounted into a docker container.
* **Branch**: a linear set of commits (one branch of the tree) and a live running point which the database can write to.
* **Commit**: a point-in-time snapshot of the running point of the current branch, named with a UUID.

# Docker integration

Use a `dvol` volume in Docker by specifying `docker run -v name:/path --volume-driver` or the equivalent `volume_driver` in Compose.

If a `dvol` volume doesn't exist when it is referenced, it is created on-demand.

# Usage

`dvol` copies `git` as closely as possible, but only implements a subset of its commands.

Here are some examples:

* `dvol list`: see which volumes there are, which branch each volume is on, and which containers are currently using each volume.
* `dvol commit -m "commit description"`: create a new commit based on the running point of the database container by safely stopping and starting the container around the commit.
* `dvol checkout -b newbranch`: create a new branch named `newbranch` from the latest commit (`HEAD`) on the current branch.
* `dvol reset --hard HEAD^`: roll back the current branch to the second last commit.

You can see all available commands by running `dvol --help`.

If you want other commands to be implemented, please [open an issue](https://github.com/clusterhq/dvol/issues/) or even better a pull request!

# Demo

[![dvol clusterhq](http://img.youtube.com/vi/aXMNp-L_-1c/0.jpg)](https://youtu.be/aXMNp-L_-1c)

## Ideas? Feedback? Issues? Bugs?

We really appreciate your ideas, feature request, pulls, and issues/bug reports for dvol, because we believe in building useful and user friendly tools for our communities.

Please raise a ticket or feel free to send us a email at [feedback@clusterhq.com](mailto:feedback@clusterhq.com).
