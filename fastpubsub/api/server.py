"""Gunicorn server configuration and startup for fastpubsub application."""

from gunicorn.app.base import BaseApplication

from fastpubsub.config import settings


class CustomGunicornApp(BaseApplication):
    """Custom Gunicorn application for running the FastAPI app.

    Extends BaseApplication to provide custom configuration and loading
    of the FastAPI application for production deployment.
    """

    def __init__(self, app, options=None):
        """Initialize the custom Gunicorn application.

        Args:
            app: The FastAPI application instance to run.
            options: Optional dictionary of Gunicorn configuration options.
        """
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        """Load configuration settings from options dictionary.

        Sets Gunicorn configuration values from the options provided during initialization.
        Only applies settings that are valid Gunicorn configuration keys.
        """
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key, value)

    def load(self):
        """Load the FastAPI application.

        Returns:
            The FastAPI application instance to be served by Gunicorn.
        """
        return self.application


def run_server(app):
    """Start the Gunicorn server with the FastAPI application.

    Configures and starts the production HTTP server using Gunicorn
    with Uvicorn workers for running the FastAPI application.

    Args:
        app: The FastAPI application instance to serve.
    """
    options = {
        "bind": f"{settings.api_host}:{settings.api_port}",
        "workers": settings.api_num_workers,
        "loglevel": settings.log_level,
        "worker_class": "uvicorn.workers.UvicornWorker",
    }
    CustomGunicornApp(app, options).run()
