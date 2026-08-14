from datetime import datetime
from uuid import uuid4


# build a name that is unique per run, so a test can be repeated (and run in parallel
# with -n) without colliding with entities left behind by an earlier execution
def unique_name(prefix: str) -> str:
    """Return a unique entity name, e.g. unique_name("br") -> 'br_20260813_141502_9f3a'."""
    return f"{prefix}_{datetime.now():%Y%m%d_%H%M%S}_{uuid4().hex[:4]}"
