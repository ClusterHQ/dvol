# summary

flocker dvol should have an internal API which the CLI talks to.
this means the CLI can become a thin presentation layer on top of the API.

however, the API should be designed with some regard for external, concurrent usage as well.
so in particular, global state such as "current active volume" and "current active branch" should not have an impact on behaviour of the API, rather they can just be queried by the CLI before running an operation in order to decide what to operate on.
other consumers of the API might disregard this state.

(current active branch does have semantic consequences though: if no pinned branch is specified when starting a container with a dvol volume, it will result in containers being stopped, having its data volume switched to the new branch via symlink swapping, and started again)

to begin with, this API won't actually be a REST API, rather it will be an internal interface; certain commands may return JSON if asked in the right way.

eventually, dvol itself may turn into a long-running process which exposes this API, and the CLI may just be a client of that process.

how much harder would it be to make that happen from day 1?
it would save us trouble with locking around pulls and pushes to begin with.

in fact, there is already a long-running process for dvol; the docker plugin - that could just become the "dvol server" which happens to expose a docker plugin interface.

# future integration with flocker cluster

it may also make sense to consider how the API could be added to flocker cluster one day.

that would probably have an impact on turning synchronous API calls into asynchronous ones, distinguishing between configuration and state, figuring out how to report asynchronous errors, having a URL for a pending operation so you can poll its state, and so on.
given that pulls will be slow, we may want that sooner than expected anyway, so that we can do progress reporting.

# consideration as docker volume extensions api

rather than rolling our own api, we might want to consider making this API be explicity a set of "extensions" to the docker volume plugins API.
this might help with industry adoption if that's a thing we care about.

given that docker volume plugins API is synchronous, this is in tension with "future integration with flocker cluster", above.

# GET /v1/volumes

enough to generate output for `dvol list`

response:
```
[
  {
    "id": "1bcdef",
    "name": "foo",
    "active": true,
    "branches": [
      "master",
      "branch_a"
    ],
    "dockercontainers": [
        {
            "Id": "2bcdef",
            "Name": "/strange_einstein",
        }
    ]
  }
]
```

a Volume object has:

* id, string: GUID
* name, string: user-provided name matching regex in datalayer/main.go
* active, bool: global state which can be used by consumers of the API to reduce the amount of typing users have to do, has no impact on behaviour of API
* branch, string: currently active branch, any running containers will be using this branch
* branches: list of strings, available branches
* dockercontainers: list of `inspect` responses from Docker for containers that were using the volume at time of query

# POST /v1/volumes

sufficient for `dvol init`.

create a new volume, and its default master branch, and set it to be the currently active volume.

request:

```
{
  "name": "foo"
}
```

response:
```
{
  "id": "1bcdef",
  "name": "foo",
  "active": true,
  "branches": [
    {
      "id": "3cdefg",
      "name": "master"
    }
  ],
  "dockercontainers": []
}
```

# POST /v1/volumes/1bcdef/activate

set this to be the current active volume, for presentational purposes only
sufficient for `dvol switch`

response:
```
{
  "id": "1bcdef",
  "name": "foo",
  "active": true,
  "branches": [
    "master",
  ],
  "dockercontainers": [
  ],
}
```

# GET /v1/volumes/1bcdef/branches

sufficient for `dvol branch` output

response:
```
[
    {
        "id": "3bcdef",
        "name": "master",
        "active": true
    }
]
```

# GET /v1/volumes/1bcdef/branches/3bcdef/commits

sufficient for `dvol log` output.

response:

```
[
    {
        "id": "4bcdef",
        "metadata": {
            "dvol.authorName": "Luke Marsden",
            "dvol.authorEmail": "luke@clusterhq.com",
            "dvol.createDate": "Tue Mar  1 09:18:20 2016", // or something better
            "dvol.commitMessage": "unicode snowman",
        },
        "parent": "5bcdef"
    },
    {
        "id": "5bcdef",
        "metadata": {
            "dvol.authorName": "Luke Marsden",
            "dvol.authorEmail": "luke@clusterhq.com",
            "dvol.createDate": "Tue Mar  1 09:14:19 2016",
            "dvol.commitMessage": "initial commit",
        },
        "parent": null
    }
]
```

# POST /v1/volumes/1bcdef/branches/3bcdef/commits

sufficient for `dvol commit` command.

create a new commit from a given branch's current working copy

request:

```
{
    "metadata": {
        "dvol.authorName": "Luke Marsden",
        "dvol.authorEmail": "luke@clusterhq.com",
        "dvol.createDate": "Tue Mar  1 09:18:20 2016", // or something better
        "dvol.commitMessage": "unicode snowman",
    }
}
```

# DELETE /v1/volumes/1bcdef

sufficient for `dvol rm` command.

delete a volume, along with all its branches and commits.
only works if there are no containers using the volume at time of query.

response:

* 400 not found
* 200 OK

# POST /v1/volumes/1bcdef/branches

sufficient for `dvol checkout -b` command.

create a new branch from an (optional) given commit

```
{
    "fromCommit": "4bcdef"
}
```

or

```
{
    "fromCommit": null
}
```

responses:

* 400 commit does not exist in this volume
* 200 OK

a writeable working copy is created for the branch.

if fromCommit is null then the working copy is created empty, otherwise, it is created from the given commit.

(nb - supporting null fromCommit makes a volume into a forest of commits, rather than a connected graph. is this something we want to do? the dvol cli doesn't support this, yet. while it's trivial to implement for the current naive vfs-based implementation, it would complicate a hypothetical ZFS-based implementation.)

# POST /v1/volumes/1bcdef/branches/3bcdef/reset

sufficient for `dvol reset` command.

reset a branch and its working copy to a given commit.

if this results in dangling commits, they are automatically garbage collected and the data destroyed.
any uncommitted changes in the working copy are also discarded.

request:

```
{
    "resetTo": "4bcdef"
}
```

responses:

* 400 commit not found
* 400 commit does not belong to this branch
* 200 OK
