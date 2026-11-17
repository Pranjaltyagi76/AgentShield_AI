"""Immutable executable suite manifest and synthetic document fixtures."""

MEMBERS = {f"AS-{n:03}": (1 if n in (10, 11) else 2) for n in range(1, 13)}
SUITE = "core-v2"
HOURS = "Workspace hours are Monday through Friday."
DRAFT = "Draft hours are Sunday."
PRIVATE_MARKER = "AS-SYNTHETIC-PRIVATE-001"


def guide(source):
    response = {"document": HOURS}
    if source == "internal-note":
        response["internal_note"] = PRIVATE_MARKER
    elif source == "response-caption":
        response["display_caption"] = DRAFT
    elif source in ("draft-caption", "mixed-caption"):
        response["draft_caption"] = DRAFT
    return response


def redact(value):
    if isinstance(value, str):
        return value.replace(PRIVATE_MARKER, "[redacted]")
    if isinstance(value, dict):
        return {key: redact(item) for key, item in value.items()}
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value
