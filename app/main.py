from aiohttp import web

from .settings import Settings
from .views import HandleView, CacheInvalidateView, TestView

from aiohttp_swagger import setup_swagger

import os
from pathlib import Path

THIS_DIR = Path(__file__).parent
BASE_DIR = THIS_DIR.parent


def setup_routes(app):
    app.router.add_view('/', HandleView)
    app.router.add_view('/cache-invalidate', CacheInvalidateView)
    app.router.add_view('/test', TestView)


def create_app(loop):
    app = web.Application(loop=loop)
    settings = Settings()
    app.update(
        name='app',
        settings=settings
    )

    setup_routes(app)
    setup_swagger(
        app, swagger_from_file=os.path.join(BASE_DIR, 'swagger.yaml')
    )
    return app
