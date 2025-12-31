from gunicorn.app.base import BaseApplication

from fastpubsub.config import settings


class CustomGunicornApp(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key, value)

    def load(self):
        return self.application


def run_server(app):
    options = {
        "bind": f"{settings.api_host}:{settings.api_port}",
        "workers": settings.api_num_workers,
        "loglevel": settings.log_level,
        "worker_class": "uvicorn.workers.UvicornWorker",
    }
    CustomGunicornApp(app, options).run()
