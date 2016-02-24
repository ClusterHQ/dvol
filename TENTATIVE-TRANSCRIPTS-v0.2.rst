Vocabulary
==========

  * A volume is a collection of branches (organized inside a project).
  * A working copy is a writeable filesystem area which starts from the data in
    a commit and can be diverged and eventually committed.

Assumptions
===========

* familiar commands are good
  * dvol push is like git push - experience transfers
* commands with fewer concepts are generally better
  * dvol undo has fewer pieces than dvol reset --hard HEAD^
* shorter commands are generally better as long as they remain descriptive
  * dvol push myusername/project/slot has the myusername component which rarely varies
* avoiding having to type your own identity is good (the computer should be able to determine it at push/pull time)

Key for transcripts
===================

  * % Logical operation, does not dictate actual UX
  * $ Literal interaction, dictates exact UX


Potential naming model for fully qualified remote names
=======================================================

* Naming dump:
  * one segment: an alias for a volume
  * two segments: an alias and a variant in the aliased volume
  * three segments: full name of a volume
  * four segments: full name of a variant
  * maybe full names should be syntactically differentiated from aliases somehow, too
    * eg ``@full_name`` vs ``alias`` (or whatever)
  * Leave name off commands if DVOL_VOLUME is set in the environment

Divergences from git
====================

Ways in which it's OK to diverge from ``git`` syntax and/or semantics, with reasons:

* ``dvol clone`` not pulling down the entire repo.
  Because ``dvol`` deals with data, which is likely to be orders of magnitude larger than code, it's more appropriate to initially only pull down metadata and distinguish between locally absent and present commits (or branches) in the UI.
* Existence of ``dvol switch`` and ``dvol projects``.
  Git users put projects into directories and organize them however they see fit.
  Because dvol doesn't check things out into local directories, users cannot use this organizational structure.
  Therefore, we need to replace ``cd`` with ``dvol switch`` and ``mkdir -p Projects/microservice/database`` with something like ``dvol projects`` and its various subcommands.


key CLI experiences that are possible with 0.1 already
======================================================


active volume
-------------

Initial design was:

   $ dvol commit -m "empty state" foo

ie always name the volume on every command.

Specifying the volume every time got really tiring really quickly.
This was probably exacerbated by the fact that ``git commit`` muscle memory gets hampered by this all the time.

Possible solutions:

   $ export DVOL_VOLUME=foo/bar
   $ dvol commit -m "empty state"

   $ cd foo_project
   $ dvol commit -m "empty state"


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
OAuth2 Browser Experience, detailed elsewhere (TBD)
You are now logged in as <jean-paul.calderone@clusterhq.com>.
$

successful login to private Voluminous
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
$ dvol login vh.internal.com
OAuth2 Browser Experience, detailed elsewhere (TBD)
You are now logged in as <jean-paul.calderone@clusterhq.com>.
$

failed login
~~~~~~~~~~~~
$ dvol login
Unsuccessful OAuth2 Browser Experience
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
Permission denied.  You must own the thing or the owner must make you a collaborator on the thing.
$

local volume interactions
-------------------------

successful empty volume creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

a. init creates state somewhere far away, names are identifiers to dvol only

transcript::

    % dvol login vh.internal.com
    You are now logged in as <jean-paul.calderone@clusterhq.com>.
    $ dvol init jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn my_authn_db
    Created jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn
    To work on this volume: export DVOL_VOLUME=jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn
    % dvol info my_authn_db
    UUID 123
    % dvol info jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn
    UUID 123

b. init creates a new directory and writes some identifying information

transcript::

    % dvol login vh.internal.com
    You are now logged in as <jean-paul.calderone@clusterhq.com>.
    $ dvol init jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn my_authn_db
    Created jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn
    % cd my_authn_db
    % dvol info
    UUID 123
    % dvol info jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn
    UUID 123
    %

successful empty volume creation with implicit, unknown owner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

% dvol logout
$ dvol init imaginary/pgsql_authn
Created imaginary/pgsql_authn
$

successful empty volume creation with implicit, known owner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

% dvol login
$ dvol init imaginary/pgsql_authn
Created jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn
$

remote volume interactions
--------------------------

option a
^^^^^^^^

transcript::

    $ dvol init project_a/pgsql
    $ dvol list
      VOLUME            BRANCH    REMOTE
    * project_a/pgsql   master    <none>

    $ dvol list
      VOLUME            BRANCH    REMOTE
    * project_a/pgsql   master    <none>

    $ dvol login
    You are logged in as luke@clusterhq.com

    $ dvol list
      VOLUME            BRANCH    REMOTE
    * project_a/pgsql   master    <none>

    $ dvol push
    $ dvol list
      VOLUME            BRANCH    REMOTE
    * project_a/pgsql   master    luke@clusterhq.com/project_a/pgsql

    $ dvol clone jean-paul@clusterhq.com/project_b/mysql

    $ dvol list
      VOLUME            BRANCH    REMOTE
    * project_a/pgsql   master    luke@clusterhq.com/project_a/pgsql
      project_b/mysql   master    jean-paul@clusterhq.com/project_b/mysql

    $ dvol switch project_b/mysql
    $ dvol list
      VOLUME            BRANCH    REMOTE
      project_a/pgsql   master    luke@clusterhq.com/project_a/pgsql
    * project_b/mysql   master    jean-paul@clusterhq.com/project_b/mysql

    $ dvol login volumehub.internal
    $ dvol clone bob@email.internal/project_c/redis

    $ dvol list
      VOLUME             BRANCH    VOLUME HUB            OWNER ON THAT VOLUME HUB
      project_a/pgsql    master    <default>             luke@clusterhq.com
      project_b/mysql    master                          jean-paul@clusterhq.com
    * project_c/redis    master    volumehub.internal    bob@email.internal
      project_c_x/redis  master    volumehub.pub         bob@email.internal

* project/volume name collisions could be dealt with on the client side <-
  Luke's preference, because it keeps the local namespace simple (two-level)
  which eases conceptual model and implementation complexity

  * should *projects* be the things that have globally unique identity, and remotes?
  * alternative to consider::

        $ dvol projects
        PROJECT      REMOTE (a configured target to attempt to interact with when pushing or pulling)
        project_a    luke@clusterhq.com/project_a
        project_b    jean-paul@clusterhq.com/project_b
        project_c    volumehub.internal/bob@email.internal/project_c

        $ dvol list
          VOLUME            BRANCH
          project_a/pgsql   master
          project_b/mysql   master
        * project_c/redis   master

Possible way to disambiguate (following on example from above)::

    $ dvol clone someone@else.com/project_b/rabbit
    Conflict: project_b is already a configured local project. Use:
       dvol clone [<volumehub>/]<user>/<project>/<repo> <localproject>/<repo>
    to clone it to a different local project namespace.

    $ dvol clone someone@else.com/project_b/rabbit project_a_someone_else/rabbit

* OR, they could only be dealt with when there's a conflict by forcing the user to spell the long form remote
* OR, you can skip typing your name and just have to type everyone else's name

option b
^^^^^^^^
$ dvol init project_a/pgsql
$ dvol list
OWNER                  PROJECT     VOLUME
luke@clusterhq.com     project_a   pgsql
$
$ dvol clone jean-paul@clusterhq.com/project_b/mysql
$ dvol list
OWNER                    PROJECT           VOLUME
luke@clusterhq.com       project_a         pgsql
jean-paul@clusterhq.com  project_b         mysql
$ dvol login
You are logged in as luke@clusterhq.com
$ dvol push project_a/pgsql
$ dvol list
OWNER                    PROJECT           VOLUME
luke@clusterhq.com       project_a         pgsql
jean-paul@clusterhq.com  project_b         mysql
$

cloning someone else's repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Axes for consideration:
  a. Can you download metadata by itself or only metadata and data?
  b. How do you disambiguate between two projects with the same name and different owners?
  c. How broadly or narrowly can you scope the download (project, volume, variant, commit)?

* Itamar & Jean-Paul's best guess: (a2 now, a1 later) b2 c4

a1. Download metadata by itself
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

a2. Download metadata and data together
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

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

b1. Use full name always
^^^^^^^^^^^^^^^^^^^^^^^^
% dvol info jean-paul@clusterhq.com/project_b/mysql
UUID 123
% dvol info luke@clusterhq.com/project_b/mysql
UUID 456
%

b2. Set up aliases
^^^^^^^^^^^^^^^^^^
% dvol alias-remote luke-mysql luke@clusterhq.com/project_b/mysql
% dvol alias-remote jp-mysql jean-paul@clusterhq.com/project_b/mysql
% dvol info luke-mysql
UUID 456
% dvol info jp-mysql
UUID 123
%

b3. DWIM
^^^^^^^^
% dvol clone luke@clusterhq.com/project_b/mysql
% dvol info mysql
UUID 456
% dvol clone jean-paul@clusterhq.com/project_b/mysql
% dvol info mysql
Ambiguous, do you mean luke@clusterhq.com/project_b/mysql or jean-paul@clusterhq.com/project_b/mysql?
% dvol info jean-paul@clusterhq.com/project_b/mysql
UUID 123
%

* Troubles with DWIM: Conflicts with supporting referring to different sized
  collections by leaving off parts of the name.  eg, is `project_b` a project
  name or a volume name or a variant name?

b4. DWIM & Aliases
^^^^^^^^^^^^^^^^^^
% dvol clone luke@clusterhq.com/project_b/mysql
% dvol info mysql
UUID 456
% dvol clone jean-paul@clusterhq.com/project_b/mysql
% dvol info mysql
Ambiguous, do you mean luke@clusterhq.com/project_b/mysql or jean-paul@clusterhq.com/project_b/mysql?
% dvol alias-remote jp-mysql jean-paul@clusterhq.com/project_b/mysql
% dvol info jp-mysql
UUID 123
% dvol info mysql
Ambiguous, do you mean luke@clusterhq.com/project_b/mysql or jp-mysql?
% dvol alias-remote luke-mysql luke@clusterhq.com/project_b/mysql
% dvol info luke-mysql
UUID 456
%

* Same DWIM trouble as above.

b5. Don't support ambiguity
^^^^^^^^^^^^^^^^^^^^^^^^^^^
% dvol clone luke@clusterhq.com/project_b/mysql
% dvol clone jean-paul@clusterhq.com/project_b/mysql
ERROR You already have project_b/mysql.  Rename something to proceed. (clone failed)
%

c1. All owner's projects (Everything)
c2. All of one owner's project's volumes (All of one project)
c3. All of one owner's project's volume's variants (All of one volume)
c4. All of one owner's project's volume's variant's commits (All of one variant)
c5. Some of one owner's project's volume's variant's commits (1..N) (Some data belonging to one variant)

(sort of different ideas)
c6. dvol pull-variants foo/bar test-data
c7. dvol pull 'foo/bar/*/test-data'
c8. dvol pull 'search(owner=foo,project=bar,variant=test-data)' (Some stuff)
c9. dvol pull foo/bar/volume

push
~~~~
$ dvol login vh.internal.com
You are now logged in as <jean-paul.calderone@clusterhq.com>.
% dvol init jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn my_authn_db
$ dvol push my_authn_db
Pushed to jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn on vh.internal.com
$

push a volume created before registering with volumehub
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

a. ???

transcript::

  

push just one variant
~~~~~~~~~~~~~~~~~~~~~
$ dvol push my_authn_db/testing_v3
Pushed to jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn/testing_v3 on vh.internal.com
$

push latest commit on branch and all metadata on branch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
$ dvol push --latest my_authn_db/testing_v3
Pushed my_authn_db/testing_v3 @ abcdefghi
$

push with divergence
~~~~~~~~~~~~~~~~~~~~
$ dvol push my_authn_db
Sorry, you've diverged. Pick a new name for local version [originalvariant-modified]:
OK your local changes are now "originalvariant-modified".
Pushed version is "originalvariant-modified".
$

pull with divergence
~~~~~~~~~~~~~~~~~~~~
$ dvol pull jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn
Sorry, you've diverged. Pick a new name for local version [originalvariant-modified]:
OK your local changes are now "originalvariant-modified".
Pulled version is "originalvariant".
$

pull with divergence in a working copy
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
$ dvol pull jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn
Sorry, the working copy for jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn/testing_v3 has diverged from the branch.  Please:
  a) throw away working copy changes
  b)  XXXXX????????? (pull failed ???????)
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

branches
--------
According to the spec, essentially not in scope, but this is surely an oversight.

commit
------

record some changes to an existing variant in a new commit
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
$ dvol commit my_authn_db -m “blah blah blah”
$

dvol docker volume plugin interaction examples
----------------------------------------------

use a variant as a docker container volume
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

$ docker run \
        --detach \
        --volume-driver \
        dvol \
        --volume \
        jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn/staging:/var/lib/pgsql
        postgresql:7.1
ffffcontaineridffff
$

try to get a working copy based on a commit that is not stored locally
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
$ docker run -v project_b/mysql:/foo --volume-driver=dvol ...
Error: no data in project_b/mysql yet, run dvol pull project_b/mysql/master
% dvol list-branches
BRANCH                                            DATA LOCAL
jean-paul@clusterhq.com/project_b/mysql/master    no
% dvol pull project_b/mysql/master
$ docker run -v project_b/mysql:/foo --volume-driver=dvol ...
deadbeefdeadbeef
$


create a working copy that may be demand-paged from a remote snapshot
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

$ docker volume create \
        --name messing-around \
        --volume-driver dvol \
        --opts paging=demand,branch=jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn/staging
abcdef0123456789
$ docker run \
        --detach \
        --volume-driver \
        dvol \
        --volume messing-around:/var/lib/pgsql
        postgresql:7.1
ffffcontaineridffff
$

changing the branch used by already running containers
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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
    $ dvol checkout -b branch_a
    $ pgsql <talk to that container> -c "SELECT * FROM foo"
    0 rows
    $ dvol checkout master
    $ pgsql <talk to that container> -c "SELECT * FROM foo"
    bar
    1 rows
    $
