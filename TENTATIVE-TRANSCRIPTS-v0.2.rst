Vocabulary
==========

  * A volume is a collection of branches (organized inside a project).
    * A volume is referred to locally by an opaque name assigned by the user (with a default sometimes)
    * A volume is referred to remotely by a hierarchical name of the form
      ``owner/name`` where the ``owner`` component is a Voluminous username and
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

  * always in the form: ``[<volumehub-address>/]<user>/<repo-name>``

  .. note::

     (Luke) where <repo-name> *cannot* contain a ``/``?

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

$ dvol <push, pull, etc, with any valid options>
Permission denied.  Please log in using dvol login.
$

successful login to hosted Voluminous
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
$ dvol login
<OAuth2 Browser Experience, detailed elsewhere (TBD)>
You are now logged in as <jean-paul.calderone@clusterhq.com>.
$

successful login to private Voluminous
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
$ dvol login vh.internal.com
<OAuth2 Browser Experience, detailed elsewhere (TBD)>
You are now logged in as <jean-paul.calderone@clusterhq.com>.
$

failed login
~~~~~~~~~~~~
$ dvol login
<Unsuccessful OAuth2 Browser Experience>
Login failed.  Please try again.
$

logout
~~~~~~
$ dvol logout
You are now logged out.
$

authorization
-------------

unauthorized voluminous interaction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
$ dvol push someone.else@somewhere.else/theirproject/their_thing
Permission denied.  You must own the thing or the owner must make you a collaborator on the thing. <link to docs on collaborators>
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

b2x. Set up aliases in the clone (or init) command
**************************************************

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

c3. All of one owner's volume's branchs (All of one volume)

a2. Download metadata and data together
***************************************

transcript::

    % dvol login
    $ dvol clone jean-paul@clusterhq.com/project_b/mysql
    <completes slowly>
    % dvol list
    VOLUME
    project_b/mysql
    % dvol list-branches
    BRANCH                                            DATA LOCAL
    jean-paul@clusterhq.com/project_b/mysql/master    yes
    jean-paul@clusterhq.com/project_b/mysql/testing   yes
    $


milestone 2: clone copies metadata, then user can choose what data to actually pull
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``dvol pull`` option:

c4. All of one owner's volume's branch's commits (All of one branch)

a1. Download metadata by itself
*******************************

transcript::

    % dvol login
    $ dvol get-metadata jean-paul@clusterhq.com/project_b/mysql
    <completes quickly>
    % dvol list
    VOLUME
    project_b/mysql
    % dvol list-branches
    BRANCH                                            DATA LOCAL
    jean-paul@clusterhq.com/project_b/mysql/master    no
    jean-paul@clusterhq.com/project_b/mysql/testing   yes
    $


cloning a repository with some kind of name collision
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
transcript::

    % dvol init foo
    % dvol clone jean-paul.calderone@clusterhq.com/foo
    You can't do that because you have a foo already.  Try `dvol clone remote_name local_name`.
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

    (Luke) I changed this to use a space rather than a / because if we allow /s in local aliases, we can't reliably figure out whether users mean branches any more.

transcript::

    $ dvol push my_authn_db testing_v3
    Pushed to jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn testing_v3 branch on vh.internal.com
    $

push with divergence
~~~~~~~~~~~~~~~~~~~~

transript::

    $ dvol push my_authn_db
    Sorry, you've diverged. Pick a new name for local version [originalbranch-modified]:
    OK your local changes are now "originalbranch-modified".
    Pushed version is "originalbranch-modified".
    $

alternative, guide the user in using git style commands to resolve conflict::

    $ dvol push my_authn_db
    Unable to push, your local tree has diverged from the remote.
    There are 3 local commits and 2 remote commits.
    You can resolve this by "renaming" your current branch, and pushing again:

        dvol checkout -b new-branch
        dvol push

.. note::

    (Luke) Should we support force-pushing the deletion of certain commits?

pull with divergence
~~~~~~~~~~~~~~~~~~~~

transript::

    $ dvol pull jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn
    Sorry, you've diverged. Pick a new name for local version [originalbranch-modified]:
    OK your local changes are now "originalbranch-modified".
    Pulled version is "originalbranch".
    $

alternative, guide the user in using git style commands to resolve conflict::

    $ dvol push my_authn_db
    Unable to push, your local tree has diverged from the remote.
    There are 3 local commits and 2 remote commits.
    You can resolve this by "renaming" your current branch:

        dvol checkout -b new-branch
        dvol checkout <current-branch>
        dvol reset --hard HEAD^^^
        dvol pull

pull with divergence in a working copy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    (Luke) This needs more thought. Currently there's no way to detect whether a working copy has diverged or not, because we never actually look at the data.
    I suggest the behaviour could be that pulls always clobber local changes, with appropriate warning/prompts.
    Alternatively, we could mark a volume as "dirty" if a container is ever started on it.
    Then we could only warn/prompt users in that case.

no update
^^^^^^^^^

transcript::

    $ dvol pull jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn
    No new commits on remote, doing nothing.
    $

new commits on remote
^^^^^^^^^^^^^^^^^^^^^

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

submit feedback
~~~~~~~~~~~~~~~
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

checkout
--------

TODO

reset
-----

TODO

branch
------
According to the spec, essentially not in scope, but this is surely an oversight.

commit
------

record some changes to an existing branch in a new commit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

a. explicitly name the volume

transcript::

  $ dvol commit ${IDENTIFIER} -m “blah blah blah”
  $

Observations:
  * Tedious in practice
  * Breaks ``git commit`` analogy

b. name the volume with an environment variable

transcript::

   $ export DVOL_VOLUME=${IDENTIFIER}
   $ dvol commit -m "empty state"

c. name the volume with working directory state

transcript::

   $ cd ${IDENTIFIER} # Previously created by ``dvol init`` or ``dvol clone``
   $ dvol commit -m "empty state"

d. implicitly selected volume based on global state

transcript::

  $ dvol switch ${IDENTIFIER}
  $ dvol commit -m "empty state"

Observations::
  * Compromises multi-use situations (global state) (perhaps relevant to CI)


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
