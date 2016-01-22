[![Build Status](https://travis-ci.org/ClusterHQ/dvol.svg?branch=master)](https://github.com/ClusterHQ/dvol)

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

# Usage

`dvol` copies `git` as closely as possible, but only implements a subset of its commands.

Here are some examples:

* `dvol list`: see which volumes there are, which branch each volume is on, and which containers are currently using each volume.
* `dvol commit -m "commit description"`: create a new commit based on the running point of the database container by safely stopping and starting the container around the commit.
* `dvol checkout -b newbranch`: create a new branch named `newbranch` from the latest commit (`HEAD`) on the current branch.
* `dvol reset --hard HEAD^`: roll back the current branch to the second last commit.

You can see all available commands by running `dvol --help`.

If you want other commands to be implemented, please [open an issue](https://github.com/clusterhq/dvol/issues/) or even better a pull request!

# Docker integration

Use a `dvol` volume in Docker by specifying `docker run -v demo:/path --volume-driver=dvol`.
This will create a dvol volume called `demo`.

If a `dvol` volume doesn't exist when it is referenced, it is created on-demand.

# Compose integration

You can also use `dvol` with [Docker Compose](https://docs.docker.com/compose/), which makes for an awesome way to spin up reproducible microservices environments on your laptop.
With `dvol` you can set `volume_driver: dvol` in order to automatically spin up all the `dvol` volumes for your app described with Docker compose with a single `docker-compose up -d`.

See [this example](https://github.com/ClusterHQ/dvol/blob/master/demos/moby-dock/docker-compose.yml) for a very simple demo.

# Demo

[![dvol clusterhq](http://img.youtube.com/vi/aXMNp-L_-1c/0.jpg)](https://youtu.be/aXMNp-L_-1c)

# Examples

Check out the [examples](https://github.com/ClusterHQ/dvol/tree/master/demos) directory.

Just run `docker-compose up -d` on any one of the `docker-compose.yml` files there.

## Ideas? Feedback? Issues? Bugs?

We really appreciate your ideas, feature request, pulls, and issues/bug reports for dvol, because we believe in building useful and user friendly tools for our communities.

Please raise a ticket or feel free to send us a email at [feedback@clusterhq.com](mailto:feedback@clusterhq.com).
