"""pyclimacell helper functions."""

import asyncio
from functools import wraps


def async_to_sync(f):
    """Decorator to run async function as sync."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        return asyncio.run(f(*args, **kwargs))

    return wrapper
