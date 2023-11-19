from logging.config import dictConfig

from app import app
from routes import setup_routes
from settings import LOG_LEVEL

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "stdout": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "default",
            },
            "stderr": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stderr",
                "formatter": "default",
                "level": "ERROR",
            },
        },
        "root": {"level": LOG_LEVEL, "handlers": ["stdout"]},
    }
)

setup_routes()

if __name__ == "__main__":
    app.run()
