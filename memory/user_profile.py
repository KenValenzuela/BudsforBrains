import os
import json

PROFILE_PATH = os.path.join(os.path.dirname(__file__), "user_profile.json")


def load_user_profile():
    """Load user profile from disk if available, otherwise return empty dict."""
    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_profile(profile_data):
    """Save user profile to disk."""
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile_data, f, indent=2)


def update_user_profile(updates, merge=True):
    """
    Update or replace the user profile.

    Args:
        updates (dict): The updates to apply.
        merge (bool): If True, merge into existing profile; if False, replace it.
    """
    if not isinstance(updates, dict):
        raise ValueError("updates must be a dictionary")

    if merge:
        profile = load_user_profile()
        profile.update(updates)
    else:
        profile = updates

    save_profile(profile)
    return profile
