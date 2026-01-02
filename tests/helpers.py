import asyncio


def sync_call_function(service, *args, **kwargs):
    """Helper function to run async functions in sync tests."""
    return asyncio.run(service(*args, **kwargs))
