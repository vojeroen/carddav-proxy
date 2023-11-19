from logging.config import dictConfig

from flask import Flask

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

app = Flask(__name__)
