Developing dvol
---------------

If you wish to work on dvol, you'll first need [Go](http://www.golang.org) installed on your machine (version 1.6+ is *required*).

For local development, firstly ensure Go is fully installed, and that you have set up a [GOPATH](http://golang.org/doc/code.html#GOPATH).
You will also need to add `$GOPATH/bin` to your `$PATH`.

Next, clone this repository using [Git](https://git-scm.com/), into `$GOPATH/src/github.com/ClusterHQ/dvol`.
All the necessary Golang dependencies are vendored, but you will need to install the following Python dependancies and Golang tools:

```sh
$ make bootstrap
```

To compile dvol:

```sh
$ make build
```

To run the tests:

```sh
$ make test
```

### Dependencies

Dvol stores its dependencies under `vendor/`, which [Go 1.6+ ](https://golang.org/cmd/go/#hdr-Vendor_Directories) will automatically recognize and load.
ClusterHQ uses [`godep`](https://github.com/tools/godep) to manage the vendored dependencies.

If you're developing dvol, there are a few tasks you might need to perform:

#### Adding a dependency

If you're adding a dependency, you'll need to vendor it in the same Pull Request as the code that depends on it.
You should do this in a separate commit from your code, as it makes it easier to review the PR, and simpler to read Git history in the future.

Because godep captures new dependencies from the local `$GOPATH`, you first need to run `godep restore` from the master branch, to ensure that the only diff is your new dependency.

Assuming your work is on a branch called `my-feature-branch`, the steps will look like this:

```bash
# Get latest master branch's dependencies staged in local $GOPATH
git checkout master
git pull
godep restore -v # flag is optional, enables verbose output

# Capture the new dependency referenced from my-feature-branch
git checkout my-feature-branch
git rebase master
godep save ./...

# There should now be changes in `vendor/` with added files for your dependency,
# and changes in Godeps/Godeps.json with metadata for your dependency.

# Make a commit with your new dependencies added
git add -A
git commit -m "vendor: Capture new dependency upstream-pkg"

# Push to your branch (may need -f if you rebased)
git push origin my-feature-branch
```

#### Updating a dependency

If you're updating an existing dependency, godep provides a specific command to snag the newer version from your `$GOPATH`:

```bash
# Update the dependancy to the version currently in your $GOPATH
godep update github.com/some/dependency/...

# There should now be changes in `vendor/` with changed files for your dependency,
# and changes in Godeps/Godeps.json with metadata for the updated dependency.

# Make a commit with the updated dependency
git add -A
git commit -m "vendor: Update dependency upstream-pkg to 1.4.6"

# Push to your branch
git push origin my-feature-branch

