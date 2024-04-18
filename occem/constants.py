import os
import sys

APP_NAME = "occem"

ROOT_PATH = os.path.join(os.path.dirname(sys.argv[0]), APP_NAME + "Data")

TEMP_PATH = os.path.join(ROOT_PATH, "temp")

LOG_PATH = os.path.join(ROOT_PATH, "logs")
