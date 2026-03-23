from loguru import logger
import os

_SERVICES_DIR = os.path.dirname(__file__)
_BACKEND_DIR = os.path.abspath(os.path.join(_SERVICES_DIR, ".."))
LOG_DIR = os.getenv("LOG_DIR", os.path.join(_BACKEND_DIR, "logs"))
LOG_FILE = os.getenv("LOG_FILE", os.path.join(LOG_DIR, "app.log"))
LOG_ENQUEUE = os.getenv("LOG_ENQUEUE", "false").lower() == "true"

_log_parent = os.path.dirname(LOG_FILE)
if _log_parent:
    os.makedirs(_log_parent, exist_ok=True)

logger.add(LOG_FILE, rotation="1 week", retention="4 weeks", enqueue=LOG_ENQUEUE)
