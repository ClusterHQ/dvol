# Preamble
# ========
# Considering only a single volume, what are the metadata and data consequences of each proposed dvol interaction?
# This is not a dvol UI/UX design document.
# dvol interactions described here probably exist in some form in the dvol 0.2 UI but not necessarily exactly as described here
# (hopefully close enough that there are no data/metadata consequences, though).

# Conventions:

# ``$ dvol <cli interaction>``:
# Something you can do with dvol

# ``<type:value>``:

# A sample value.
# ``type`` gives an idea of the range.
# ``value`` gives a trivial sample meant to be easy for a human to consume for the purposes of understanding the document.
# Equality (and non-equality) of values in the document is meant to be meaningful.


# Amble
# =====


class BlobMap(CheckedPMap):
    __key_type__ = UUID
    __value_type__ = StoredBlob


class DataStore(PClass):
    # Uniquely identify this data store.
    location_id = field(type=unicode)

    # Mapping from local blob id to StoredBlob
    blobs = BlobMap()

    def output_delta(self, first_blob, last_blob):
        """
        Return bytes which can be applied to first_blob to produce second_blob.
        """

    def create_blob_from_delta(self, first_blob, delta_bytes):
        """
        Create a new blob by applying delta_bytes (from output_delta) to
        first_blob.
        """


class StoredBlob(PClass):
    # Uniquely identify this blob in the system where it is stored.
    local_id = field(type=UUID)


class MetadataStore(CheckedPMap):
    __key_type__ = unicode
    __value_type__ = unicode


def snapshots(metadata):
    snapshots = metadata[u"snapshots"]
    
    SNAPSHOT = "snapshot:"

    for (k, v) in metadata.iteritems():
        if k.startswith(SNAPSHOT):
            snapshot_id = k[len(SNAPSHOT):]
            snapshot_


def main():
    # Empty state.
    data = DataStore(location_id=u"foo")
    metadata = MetadataStore()

    # dvol 



Empty State
-----------
Local data store:
  Location id (exactly 1): <uuid:laptop-a>
  Stored blobs (any number):
    <none>

Local metadata store:
  Snapshots (any number):
    <none>

Generate first commit
---------------------

$ dvol init
$ dvol commit

Data layer interactions
~~~~~~~~~~~~~~~~~~~~~~~

CREATE-VOLUME -> <opaque:H>
SNAPSHOT-VOLUME <opaque:H> -> <blob: <uuid:A>, <uuid:C>> (???)

create_snapshot_metadata(
    parent=nil,
    blob=<blob: <uuid:A>, <uuid:laptop-a>, <uuid:C>>,
    variant_name="testing",
    more_metadata={dvol-specified arbitrary stuff, see snapshot representation below for detail},
) -> <uuid:1>

Local data store:
  Location id (exactly 1): <uuid:laptop-a>
  Stored blobs (any number):
    content id: <uuid:A>
    local id: <uuid:C>
    blob content: <bytes:...>

Local metadata store:
  Snapshots (any number):
    snapshot id (exactly 1): <uuid:1>
    parent snapshot id (0 or 1): nil (first snapshot, no parent)
    blob (0 or 1):
      content id (exactly 1): <uuid:A>
      location (any number):
        location id: <uuid:laptop-a>
        local id: <uuid:C>
    variant name (exactly 1): <text:testing>
    dvol.author-name (exactly 1): <text:Jean-Paul Calderone> (???)
    dvol.author-email (exactly 1): <text:jean-paul@clusterhq.com> (???)
    vhub.pushed (0 or 1): <push/pull record>
      by-username (0 or 1): <text:jean-paul@clusterhq.com> (???)
      at-timestamp (0 or 1): <iso8601:Mon, 6pm>
    vhub.pulled (any number): <push/pull record>

Generate a child commit
-----------------------

$ perhaps twiddle the volume
$ dvol commit

Data layer interactions
~~~~~~~~~~~~~~~~~~~~~~~

SNAPSHOT-VOLUME <opaque:H> -> <blob: <uuid:D>, <uuid:E>> (???)

create_snapshot_metadata(
    parent=<uuid:1>,
    blob=<blob: <uuid:D>, <uuid:laptop-a>, <uuid:E>>,
    variant_name="testing",
    more_metadata={dvol-specified arbitrary stuff},
) -> <uuid:2>

Local data store:
  Location id (exactly 1): <uuid:laptop-a>
  Stored blobs (any number):
    content id: <uuid:A>
    local id: <uuid:C>
    blob content: <bytes:...>

    content id: <uuid:D>
    local id: <uuid:E>
    blob content: <bytes:...>

Local metadata store:
  Snapshots (any number):
    snapshot id (exactly 1): <uuid:1>
    {exactly as above}

    snapshot id (exactly 1): <uuid:2>
    parent snapshot id (0 or 1): <uuid:1>
    blob (0 or 1):
      content id (exactly 1): <uuid:D>
      location (any number):
        location id: <uuid:laptop-a>
        local id: <uuid:E>
    variant name (exactly 1): <text:testing>
    {more dvol metadata, as elsewhere}
