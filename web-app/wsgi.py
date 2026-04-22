import sys
import logging
from main import app, startup_app

gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

bind = "0.0.0.0:8080"

startup_app()

application=app

