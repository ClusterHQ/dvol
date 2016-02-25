Other ideas from the transcript file
====================================

The following are either out of scope for the MVP, or are options for which consensus (or at least decision) seems to have favored another.

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

b. Per-container active branch state

Like above, but when you want a container to switch to a different branch, you
use some dvol command that goes and updates that container (or _those_
containers or something).

use a variant as a docker container volume
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    (Luke) I'd suggest not supporting on-demand pulls in the plugin to begin with, because it could interact badly/confusingly/undefinedly with uncommitted working copy changes.

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

.. note::

    (Luke) We only need this for "a1 & c4 later", see ``TENTATIVE-TRANSCRIPTS-v0.2.rst``.

$ docker run -v project_b/mysql:/foo --volume-driver=dvol ...
Error: no data in project_b/mysql yet, run dvol pull project_b/mysql/master
% dvol list-branches
BRANCH                                            DATA LOCAL
jean-paul@clusterhq.com/project_b/mysql/master    no
% dvol pull project_b/mysql/master
$ docker run -v project_b/mysql:/foo --volume-driver=dvol ...
deadbeefdeadbeef
$

successful empty volume creation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

a. init creates state somewhere far away, names are identifiers to dvol only

transcript::

    % dvol login vh.internal.com
    You are now logged in as <jean-paul.calderone@clusterhq.com>.
    $ dvol init imaginary/pgsql_authn
    Created imaginary/pgsql_authn
    To work on this volume: export DVOL_VOLUME=imaginary/pgsql_authn
    % dvol list
      VOLUME                BRANCH    VOLUME HUB       OWNER
    * imaginary/pgsql_authn master    <none>           <none>
    %

b. init creates a new directory and writes some identifying information

transcript::

    % dvol login vh.internal.com
    You are now logged in as <jean-paul.calderone@clusterhq.com>.
    $ dvol init imaginary/pgsql_authn
    Created imaginary/pgsql_authn
    To work on this volume: cd imaginary/pgsql_authn
    % cd imaginary/pgsql_authn
    % dvol log
    Nothing I guess.
    % dvol list
      VOLUME                BRANCH    VOLUME HUB       OWNER
    * imaginary/pgsql_authn master    <none>           <none>
    %

c. dvol stores what was global state in 0.1 in your (code) project directory instead

as (b), but with putting dvol configuration file in your code directory rather
than having a directory per volume.

Questions:

* how do you find the file?


d. global volume & branch state with env var override

f. environment variables only (for active volume)

transcript::

    $ dvol switch imaginary
    To switch your current active volume, run:

        export DVOL_VOLUME=imaginary
    $ export DVOL_VOLUME=imaginary
    $ dvol list
    ...
    * imaginary <- based on env var
      something-else
    $ dvol init hack
    Created hack
    Created hack/master
    To make this the active branch, run:

        export DVOL_VOLUME=hack

    $ dvol commit -m "hello"
    Error: no branch specified. Set one with: export DVOL_BRANCH=foo


successful empty volume creation with implicit, known owner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. note::

    (Luke) not needed because local names (aliases) never include owner now.

% dvol login
$ dvol init imaginary/pgsql_authn
Created jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn
$

cloning someone else's repository
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

* Itamar & Jean-Paul's best guess: (a2 now, a1 later) b2 c4

push
~~~~
$ dvol login vh.internal.com
You are now logged in as <jean-paul.calderone@clusterhq.com>.
% dvol init jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn my_authn_db
$ dvol push my_authn_db
Pushed to jean-paul.calderone@clusterhq.com/imaginary/pgsql_authn on vh.internal.com
$

b1. Use full name always
************************
% dvol info jean-paul@clusterhq.com/project_b/mysql
UUID 123
% dvol info luke@clusterhq.com/project_b/mysql
UUID 456
%

b2. Set up aliases
******************
% dvol alias-remote luke-mysql luke@clusterhq.com/project_b/mysql
% dvol alias-remote jp-mysql jean-paul@clusterhq.com/project_b/mysql
% dvol info luke-mysql
UUID 456
% dvol info jp-mysql
UUID 123
%



b3. DWIM
********
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
  name or a volume name or a branch name?

b4. DWIM & Aliases
******************
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
***************************
% dvol clone luke@clusterhq.com/project_b/mysql
% dvol clone jean-paul@clusterhq.com/project_b/mysql
ERROR You already have project_b/mysql.  Rename something to proceed. (clone failed)
%



(sort of different ideas)
c6. dvol pull-variants foo/bar test-data
c7. ``dvol pull 'foo/bar/*/test-data'``
c8. dvol pull 'search(owner=foo,project=bar,variant=test-data)' (Some stuff)
c9. dvol pull foo/bar/volume


push latest commit on branch and all metadata on branch
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
$ dvol push --latest my_authn_db/testing_v3
Pushed my_authn_db/testing_v3 @ abcdefghi
$

