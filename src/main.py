import logging

from app import app
from routes import setup_routes

logger = logging.getLogger(__name__)

setup_routes()

if __name__ == "__main__":
    logger.info("starting app")
    app.run()
