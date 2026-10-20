"""Record ``kind`` names in the ``records`` table. Shared by lanes A and C so
both write and read the same rows. Add new kinds here; never rename."""

CYCLE = "cycle"
SNAPSHOT = "snapshot"  # id = cycle id; json = full snapshot as loaded (immutable per version)
EXCEPTION = "exception"
MESSAGE_BATCH = "message_batch"  # lane C writes
INBOUND = "inbound"  # lane C writes
PARSED_REPLY = "parsed_reply"  # lane C writes, id = inbound id
RESOLUTION = "resolution"  # lane C writes
CORRECTION = "correction"  # lane A/B write
WORKBOOK = "workbook"
