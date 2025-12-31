import asyncio


def sync_call_service(service, *args, **kwargs):
    """Helper function to run async services in sync tests."""
    return asyncio.run(service(*args, **kwargs))
