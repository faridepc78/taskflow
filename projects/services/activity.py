"""Compatibility shim for the old manual activity calls.

Activity logging is now automatic through model signals. Keeping this function as a
no-op avoids duplicate entries while older views are migrated naturally.
"""


def log_activity(**kwargs):
    return None
