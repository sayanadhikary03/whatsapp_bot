from fastapi import FastAPI
from app.config import load_configurations, configure_logging
from .views import router


def create_app():
    app = FastAPI(title="WhatsApp Bot API")

    # Load configurations and logging settings
    load_configurations(app)
    configure_logging()

    # Include routers
    app.include_router(router)

    return app
