import os
ALLOWED_ORIGINS = [os.getenv("BASE_URL", "")]
MAX_STEPS = 30
CONFIRM_ACTIONS = ["disable", "delete", "revoke"]
TASK_TIMEOUT_SECONDS = 120


def is_allowed_url(url: str) -> bool:
    """Only allow navigation within the admin panel."""
    return any(origin in url for origin in ALLOWED_ORIGINS)


def requires_confirmation(action_label: str) -> bool:
    """Actions that should pause for human confirmation."""
    return any(word in action_label.lower() for word in CONFIRM_ACTIONS)