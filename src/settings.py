import os

LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG").upper()
UPSTREAM_SERVER = os.environ.get("UPSTREAM_SERVER")
THIS_SERVER = os.environ.get("THIS_SERVER")
STRIP_HEADERS_TO_UPSTREAM = "host"
STRIP_HEADERS_FROM_UPSTREAM = "transfer-encoding", "content-encoding"
