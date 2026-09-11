from pathlib import Path
from logging.config import dictConfig


BASE_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = BASE_DIR / "logs"

LOG_DIR.mkdir(exist_ok=True)


def setup_logging() -> None:
    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,

            "formatters": {
                "default": {
                    "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                },
            },

            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "INFO",
                    "formatter": "default",
                },

                "file": {
                    "class": "logging.handlers.TimedRotatingFileHandler",
                    "filename": str(LOG_DIR / "carwise.log"),
                    "when": "midnight",
                    "interval": 1,
                    "backupCount": 7,
                    "encoding": "utf-8",
                    "level": "INFO",
                    "formatter": "default",
                },
            },

            "root": {
                "level": "INFO",
                "handlers": ["console", "file"],
            },
        }
    )