Vocabulary
==========

  * A volume is a collection of branches (organized inside a project).
    * A volume is referred to locally by an opaque name assigned by the user (with a default sometimes)
    * A volume is referred to remotely by a hierarchical name of the form
      ``owner/name`` where the ``owner`` component is a Volume Hub username and
      the ``name`` is like the local name above.
  * A working copy is a writeable filesystem area which starts from the data in
    a commit and can be diverged and eventually committed.

Assumptions
===========

* familiar commands are good
  * dvol push is like git push - experience transfers
* commands with fewer concepts are generally better
  * dvol undo has fewer pieces than dvol reset --hard HEAD^ (but is more ambiguous to those who understand the latter)
* shorter commands are generally better as long as they remain descriptive
  * dvol push myusername/project/slot has the myusername component which rarely varies
* avoiding having to type your own identity is good (the computer should be able to determine it at push/pull time)

Key for transcripts
===================

  * % Logical operation, does not dictate actual UX
  * $ Literal interaction, dictates exact UX


Naming model for local and remote names
=======================================

* Local names (maybe "aliases")

  * opaque string which may have ``/``s in it, so that users can self-organize their projects/microservices/whatever
  * may be set to sensible defaults by e.g. ``dvol clone``

* Remote names

  * always in the form: ``<user>/<volume-name>``

  .. note::

     Where <volume-name> may contain a ``/``
     Commands which need to refer to the location of the remote will do so separately.


Divergences from git
====================

Ways in which it's OK to diverge from ``git`` syntax and/or semantics, with reasons:

* ``dvol clone`` not pulling down the entire repo (in latter case "a1 & c4", see below).
  Because ``dvol`` deals with data, which is likely to be orders of magnitude larger than code, it's more appropriate to initially only pull down metadata and distinguish between locally absent and present commits (or branches) in the UI.
* Existence of ``dvol switch``.
  Git users put projects into directories and organize them however they see fit.
  Because dvol doesn't check things out into local directories, users cannot use this organizational structure.
  Therefore, we need to replace ``cd`` with ``dvol switch``.


dvol 0.2 cli transcript samples
===============================

authentication
--------------

unauthenticated (not logged in) voluminous interaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

transcript::

    $ dvol <push, pull, etc, with any valid options>
    Permission denied.  Please log in using dvol login.
    $

successful login to hosted Volume Hub
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
transcript::

    $ dvol login
    <OAuth2 Browser Experience, detailed elsewhere (TBD)>
    You are now logged in as <jean-paul.calderone@clusterhq.com>.
    $

successful login to private Volume Hub
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
transcript::

    $ dvol login vh.internal.com
    <OAuth2 Browser Experience, detailed elsewhere (TBD)>
    You are now logged in as <jean-paul.calderone@clusterhq.com>.
    $

failed login
~~~~~~~~~~~~
transcript::

    $ dvol login
    <Unsuccessful OAuth2 Browser Experience>
    Login failed.  Please try again.
    $

logout
~~~~~~
transcript::

    $ dvol logout
    You are now logged out.
    $

authorization
-------------

unauthorized voluminous interaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
transcript::

    $ dvol push someone.else@somewhere.else/theirproject/their_thing
    Permission denied.  You must own the thing or the owner must make you a
    collaborator on the thing. <link to docs on collaborators>
    $

local volume interactions
-------------------------

successful empty volume creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Luke best guess & Jean-Paul not objecting: e

e. global volume & branch state with increased specificity support in naming

Case analysis:

* specificity for CI case
* global volume & branch state for single user single machine case

TODO write an example

successful empty volume creation with implicit, unknown owner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

transcript::

    % dvol logout
    $ dvol init imaginary/pgsql_authn
    Created imaginary/pgsql_authn
    $

remote volume interactions
--------------------------

See the vocab section for the (CLI) naming model for volumes.
(Names here have a project component but that's not meaningful to dvol.)

transcript::

    % dvol init project_a/pgsql
    % dvol list
      VOLUME             BRANCH    VOLUME HUB    OWNER
    * project_a/pgsql    master    <none>        <none>

    % dvol login
    You are logged in as luke@clusterhq.com

    % dvol list
      VOLUME             BRANCH    VOLUME HUB    OWNER
    * project_a/pgsql    master    <none>        <none>

    % dvol push
    % dvol list
      VOLUME             BRANCH    VOLUME HUB    OWNER
      project_a/pgsql    master    vh.cqh.com    luke@clusterhq.com

    % dvol clone jean-paul@clusterhq.com/project_b/mysql

    % dvol list
      VOLUME             BRANCH    VOLUME HUB    OWNER
      project_a/pgsql    master    vh.chq.com    luke@clusterhq.com
      project_b/mysql    master    vh.chq.com    jean-paul@clusterhq.com

cloning someone else's repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Axes for consideration:
  a. Can you download metadata by itself or only metadata and data?
  b. How do you disambiguate between two projects with the same name and different owners?
  c. How broadly or narrowly can you scope the download (project, volume, branch, commit)?

* Jean-Paul & Luke's best guess (a2 & c3 now [milestone 1], a1 & c4 later [milestone 2]) b2x

b2x. Set local names in the clone command
*****************************************

Note: ``init`` always sets a local name.

transcript::

    $ dvol clone luke@clusterhq.com/project_b/mysql
    $ dvol clone jean-paul@clusterhq.com/project_b/mysql jp-mysql
    % dvol list
    VOLUME             BRANCH    VOLUME HUB    OWNER
    project_b/mysql    master    vh.chq.com    luke@clusterhq.com
    jp-mysql           master    vh.chq.com    jean-paul@clusterhq.com
    $


milestone 1: pull entire volume all the time
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``dvol pull`` option:

c3. All of one owner's volume's branches (All of one volume)

a2. Download metadata and data together
***************************************

transcript::

    % dvol login
    $ dvol clone jean-paul@clusterhq.com/project_b/mysql
    <completes slowly>
    % dvol list
    VOLUME
    project_b/mysql
    % dvol branch
    BRANCH                                            DATA LOCAL
    jean-paul@clusterhq.com/project_b/mysql/master    yes
    jean-paul@clusterhq.com/project_b/mysql/testing   yes
    $

Note: UI may not need to have "DATA LOCAL" column until it's possible to have metadata for data which isn't local.

milestone 2: clone copies metadata, then user can choose what data to actually pull
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``dvol pull`` option:

c4. All of one owner's volume's branch's commits (All of one branch)

a1. Download metadata by itself
*******************************

transcript::

    % dvol login
    $ dvol clone jean-paul@clusterhq.com/project_b/mysql
    <completes quickly>
    % dvol list
    VOLUME
    project_b/mysql
    % dvol branch
    BRANCH                                            DATA LOCAL
    jean-paul@clusterhq.com/project_b/mysql/master    no
    jean-paul@clusterhq.com/project_b/mysql/testing   no
    % dvol pull jean-paul@clusterhq.com/project_b/master
    <completes somewhat slowly>
    % dvol branch
    BRANCH                                            DATA LOCAL
    jean-paul@clusterhq.com/project_b/mysql/master    yes
    jean-paul@clusterhq.com/project_b/mysql/testing   no
    $


cloning a repository with some kind of name collision
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
transcript::

    % dvol init foo
    % dvol clone jean-paul.calderone@clusterhq.com/foo
    You can't do that because you have a foo already.  Try `dvol clone
    remote_name local_name`.
    % dvol clone jean-paul.calderone@clusterhq.com/foo jp-foo
    %

push a volume to two different volume hubs
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

transcript::

    % dvol login vh.internal.com
    Logged in as jean-paul@clusterhq.com
    % dvol init project_a/pgsql
    % dvol list
      VOLUME             BRANCH    VOLUME HUB       OWNER
    * project_a/pgsql    master    <none>           <none>
    % dvol push project_a/pgsql
    % dvol list
      VOLUME             BRANCH    VOLUME HUB       OWNER
    * project_a/pgsql    master    vh.internal.com  jean-paul@clusterhq.com
    % dvol logout
    % dvol login
    Logged in as luke@clusterhq.com
    % dvol push project_a/pgsql
    % dvol list
      VOLUME             BRANCH    VOLUME HUB       OWNER
    * project_a/pgsql    master    vh.chq.com       luke@clusterhq.com
    %


push a volume created before registering with volumehub
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

transcript::

    % dvol list
      VOLUME             BRANCH    VOLUME HUB    OWNER
    * project_a/pgsql    master    <none>        <none>
    % dvol login vh.internal.com
    Logged in as jean-paul@clusterhq.com
    % dvol push project_a/pgsql
    % dvol list
      VOLUME             BRANCH    VOLUME HUB       OWNER
    * project_a/pgsql    master    vh.internal.com  jean-paul@clusterhq.com


push just one branch
~~~~~~~~~~~~~~~~~~~~~

.. note::

    (Luke) I changed this to use a space rather than a / because if we allow /s
    in local aliases, we can't reliably figure out whether users mean branches
    any more.

transcript::

    $ dvol push my_authn_db testing_v3
    Pushed to jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn
    testing_v3 branch on vh.internal.com
    $

push with divergence
~~~~~~~~~~~~~~~~~~~~

a. transript::

    $ dvol push my_authn_db
    Sorry, you've diverged. Pick a new name for local version [originalbranch-modified]:
    OK your local changes are now "originalbranch-modified".
    Pushed version is "originalbranch-modified".
    $

b. alternative, guide the user in using git style commands to resolve conflict::

    $ dvol push my_authn_db
    Unable to push, your local tree has diverged from the remote.
    There are 3 local commits and 2 remote commits.
    You can resolve this by "renaming" your current branch, and pushing again:

        dvol checkout -b new-branch
        dvol push

.. note::

    (Luke) Should we support force-pushing the deletion of certain commits?
    Currently there is no way to delete remote commits, AIUI.

pull with divergence
~~~~~~~~~~~~~~~~~~~~

a. transript::

    $ dvol pull jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn
    Sorry, you've diverged. Pick a new name for local version [originalbranch-modified]:
    OK your local changes are now "originalbranch-modified".
    Pulled version is "originalbranch".
    $

b. alternative, guide the user in using git style commands to resolve conflict::

    $ dvol pull my_authn_db
    Unable to push, your local tree has diverged from the remote.
    There are 3 local commits and 2 remote commits.
    You can resolve this by "renaming" your current branch:

        dvol checkout -b new-branch
        dvol checkout <current-branch>
        dvol reset --hard HEAD^^^
        dvol pull

.. note::

   (Jean-Paul & Itamar)
   This needs more thought.
   Even in git you cannot use ``reset --hard`` if you want to be able to collaborate with people.
   At best, you have to use ``push --force`` and everyone else has to sort out the resulting problems individually.
   No one has proposed supporting a ``dvol push --force`` so if you ever use ``dvol reset --hard HEAD^`` then you're not likely to be able to push.
   The only case where this **could** work as specified is if you haven't pushed the thing you're resetting yet.

   (Luke)
   In the current model, you're right: you'd never be able to push a branch which had diverged from the hub.
   For this iteration however I believe that having to rename your local branch before pushing is sufficient.
   Resolving conflicts locally in this way is probably fine.
   The system should be smart enough not to have to re-upload all the common commits.
   IMO, we don't know enough about how people are going to use branches and commits for data management to know if this *isn't* going to be sufficient.
   I don't want to support ``dvol push --force`` yet because it forces a problem on all other pullers of the branch.


pull with divergence in a working copy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    (Luke) This needs more thought.
    Currently there's no way to detect whether a working copy has diverged or not (XXX Yes there is.  -Jean-Paul), because we never actually look at the data.
    I suggest the behaviour could be that pulls always clobber local changes, with appropriate warning/prompts.
    Alternatively, we could mark a volume as "dirty" if a container is ever started on it.
    Then we could only warn/prompt users in that case.

    (Jean-Paul & Itamar)
    How many databases generate writes immediately upon startup, even with no application-level changes?
    Does this mean there will _always_ apparently be divergences in a working copy, but the diverged local state will frequently be irrelevant?
    How frequently?
    Does this make a difference to how we design the model or the UI?

no update
^^^^^^^^^

transcript::

    $ dvol pull jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn
    No new commits on remote, doing nothing.
    $

new commits on remote cause local data to be discarded
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

a. always warn::

    $ dvol pull jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn
    Warning there are new commits to pull: if you have uncommitted changes,
    they will be lost.
    Destroy uncommitted changes (y/n)? y
    Pulling... done.
    $

b. warn if dirty::

    $ dvol pull jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn
    Working copy clean (no containers started).
    Pulling... done.
    $

c. create a new volume to hold the locally diverged state::

   $ dvol pull jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn
   Local changes in working tree saved in new working tree "imaginary/pgsql_authn-20160302T162113.0".
   Pulling... done.
   $

d. create a new commit in a new variant to hold the locally diverged state::

   $ dvol pull jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn
   Local changes in working tree saved in new variant "testing-workingtree-20160302T162113.0".
   Pulling... done.
   $

e. merge above::

   $ dvol pull jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn
   Working tree contains modifications.
   Pull anyway ((n)o, (d)estroy modifications, save in new (v)olume, save in new (c)ommit)?
   ...


submit feedback
~~~~~~~~~~~~~~~

.. note::

    (Luke) Is this supposed to imply that ``create`` is any command that doesn't exist?

a. transcript::

    $ dvol create --help
     ....
      if istty(stdin) Do you want to send us some comments?  [Y/n/Never ask again]
      > ...
    $ dvol feedback
      > Dear ClusterHQ,
      > You're great.
      > Love,
      > The internet.
      > ^D
    $

b. alternative, dedicated feedback commands::

   $ dvol feedback
   Please let us know your feedback at https://clusterhq.com/dvol-feedback/ - thanks!
   $

checkout
--------

NB: stops containers and starts containers with the new data, see "dvol docker volume plugin interaction examples".

switch the current active branch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

acts on the currently globally active volume.
optionally, supports specifying volume with ``--volume``.
(all commands which operate on volumes should take this optional argument.)

transcript::

    $ dvol branch [--volume=specific_volume]
    * master
      another
    $ dvol checkout [--volume=specific_volume] another
    $ dvol branch [--volume=specific_volume]
      master
    * another


create a new branch from the existing branch, and switch to it
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

(eliding ``--volume`` arguments here, for readability)

transcript::

    $ dvol branch
    * master
    $ dvol checkout -b new_branch
    $ dvol branch
      master
    * new_branch

longer example showing how commits are "copied" to new branch from user's perspective, implementation will use fossil-style inherited labels::

    $ dvol branch
    * master
    $ dvol log
    commit b0c8a6067c0e4924b8c56aeef9e56b5aa6d62431
    Author: Who knows <mystery@person>
    Date: Whenever

      hello

    $ dvol checkout -b new_branch
    $ dvol branch
      master
    * new_branch
    $ dvol log
    commit b0c8a6067c0e4924b8c56aeef9e56b5aa6d62431
    Author: Who knows <mystery@person>
    Date: Whenever

      hello

nb: create the new branch from the latest commit in the branch. working copy is ignored when creating a new branch.

reset
-----

optionally takes ``--volume`` for concurrent operation.
optionally takes ``--branch`` for concurrent operation.

move ("unwind") a branch to point to a previous commit.
also reset the respective working copy to the previous commit, irrespective of whether it has any new modifications::

    $ dvol log
    commit b0c8a6067c0e4924b8c56aeef9e56b5aa6d62431
    Author: Who knows <mystery@person>
    Date: Whenever

      commit 1

    commit c0c8a6067c0e4924b8c56aeef9e56b5aa6d62431
    Author: Who knows <mystery@person>
    Date: Whenever

      commit 2

    $ dvol reset --hard b0c8a6067c0e4924b8c56aeef9e56b5aa6d62431
    $ dvol log
    commit b0c8a6067c0e4924b8c56aeef9e56b5aa6d62431
    Author: Who knows <mystery@person>
    Date: Whenever

      commit 1

if no other branches refer to that commit, automatically garbage collect the orphaned commits. (hard to show in a transcript)

do *not* delete commits when they are still referenced by another branch. see test_rollback_branch_doesnt_delete_referenced_data_in_other_branches in test_dvol.py.

reset can take a commit id, or HEAD meaning the latest commit on the branch.
0 or more ``^`` symbols may be suffixed, meaning predecessor commit, all of the following are valid::

    $ dvol reset --hard b0c8a6067c0e4924b8c56aeef9e56b5aa6d62431^
    $ dvol reset --hard HEAD
    $ dvol reset --hard HEAD^
    $ dvol reset --hard HEAD^^^^^^^^^^^

not specifying ``--hard`` is unsupported, this forces the user to acknowledge that they are performing a potentially destructive operation.

also supports any unique prefix of a commit, for example::

    $ dvol reset --hard b0c8a6
    $ dvol reset --hard b0c8a6^

branch
------

optionally takes ``--volume`` for concurrent operation.

list the branches in the current active volume.

log
---

optionally takes ``--volume`` for concurrent operation.
optionally takes ``--branch`` for concurrent operation.

list the linear commits in the current branch.

commit
------

NB: stops containers using the branch before making a commit.
Then starts them again afterwards.
This is because current directory copy mechanism isn't atomic.

record some changes to an existing branch in a new commit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

optionally takes ``--volume`` for concurrent operation.
optionally takes ``--branch`` for concurrent operation.

implicitly selected volume based on global state, but allow override for increased specificity for automated (e.g. CI) usage.

transcript::

  $ dvol switch ${IDENTIFIER}
  $ dvol commit -m "empty state"

Observations::
  * Compromises multi-use situations (global state) (perhaps relevant to CI)

ignore global state and commit a specific volume name::

  $ dvol commit -m "empty state" --volume mything/no_race_conditions_here


dvol docker volume plugin interaction examples
----------------------------------------------

changing the branch used by already running containers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

a. Global per-volume active branch state

A container is run using the name of a volume.
A working copy is supplied based on the "checked out" branch of the volume.
``dvol checkout`` is how the "checked out" branch is controlled.
"Checked out" branch is a global property of each volume.

transcript::

    % docker run \
            --detach \
            --volume-driver \
            dvol \
            --volume ${VOLUME_NAME}:/var/lib/pgsql
            postgresql:7.1
    ffffcontaineridffff
    % pgsql <talk to that container> -c 'INSERT INTO foo VALUES ("bar")'
    % dvol commit -m "Foo and bar"
    % dvol checkout -b branch_a
    $ pgsql <talk to that container> -c "SELECT * FROM foo"
    0 rows
    % dvol checkout master
    $ pgsql <talk to that container> -c "SELECT * FROM foo"
    bar
    1 rows
    $
