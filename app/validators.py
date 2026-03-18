
from app.models import VALID_PRIORITIES, VALID_STATUSES


def validate_create(data: dict) -> list:
    errors = []

    if not isinstance(data, dict):
        return ["Request body must be a JSON object"]

    if "title" not in data or data["title"] is None:
        errors.append("'title' is required")
    elif not isinstance(data["title"], str):
        errors.append("'title' must be a string")
    elif len(data["title"].strip()) == 0:
        errors.append("'title' cannot be blank")
    elif len(data["title"]) > 200:
        errors.append("'title' must be 200 characters or fewer")

    if "description" in data and data["description"] is not None:
        if not isinstance(data["description"], str):
            errors.append("'description' must be a string")

    if "status" in data and data["status"] not in VALID_STATUSES:
        errors.append(f"'status' must be one of: {list(VALID_STATUSES)}")

    if "priority" in data and data["priority"] not in VALID_PRIORITIES:
        errors.append(f"'priority' must be one of: {list(VALID_PRIORITIES)}")

    return errors


def validate_update(data: dict) -> list:

    errors = []

    if not isinstance(data, dict) or not data:
        errors.append("Request body must be a non-empty JSON object")
        return errors

    known   = {"title", "description", "status", "priority", "due_date"}
    unknown = set(data.keys()) - known
    if unknown:
        errors.append(f"Unknown field(s): {sorted(unknown)}")

    if "title" in data:
        if not isinstance(data["title"], str):
            errors.append("'title' must be a string")
        elif len(data["title"].strip()) == 0:
            errors.append("'title' cannot be blank")
        elif len(data["title"]) > 200:
            errors.append("'title' must be 200 characters or fewer")

    if "description" in data and data["description"] is not None:
        if not isinstance(data["description"], str):
            errors.append("'description' must be a string")

    if "status" in data and data["status"] not in VALID_STATUSES:
        errors.append(f"'status' must be one of: {list(VALID_STATUSES)}")

    if "priority" in data and data["priority"] not in VALID_PRIORITIES:
        errors.append(f"'priority' must be one of: {list(VALID_PRIORITIES)}")

    return errors
