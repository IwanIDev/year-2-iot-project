import sys
import logging
from main import app

logging.basicConfig(stream=sys.stderr)

bind = "0.0.0.0:8080"

application=app

