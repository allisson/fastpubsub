"""Helper functions for test utilities."""

import asyncio


def sync_call_function(service, *args, **kwargs):
    """Helper function to run async functions in sync tests.

    Args:
        service: Async function to call.
        *args: Positional arguments to pass to the async function.
        **kwargs: Keyword arguments to pass to the async function.

    Returns:
        Result of the async function execution.
    """
    return asyncio.run(service(*args, **kwargs))
