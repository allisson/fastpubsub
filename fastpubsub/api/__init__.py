from fastpubsub.api.app import create_app
from fastpubsub.api.server import run_server

# Create the app instance for backward compatibility and testing
app = create_app()

__all__ = ["create_app", "run_server", "app"]
