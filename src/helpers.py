import logging
from base64 import b64decode, b64encode

from flask import request

logger = logging.getLogger(__name__)


def log_downstream_request():
    logger.debug(f"downstream request method: {request.method}")
    logger.debug(f"downstream request content: {request.data}")
    logger.debug(f"downstream request headers: {request.headers}")
    logger.debug(f"downstream request cookies: {request.cookies}")


def split_username(username):
    try:
        username, addressbook = username.split("#")
    except ValueError:
        addressbook = ""
    return username, addressbook


def process_authorization_header():
    upstream_request_headers = {k: v for k, v in request.headers.items()}

    try:
        authorization_header = request.headers["authorization"]
        authorization_type, credentials = authorization_header.split(" ")
        if authorization_type.lower() != "basic":
            return "", "", upstream_request_headers
        username, password = b64decode(credentials).decode().split(":")
        logger.debug(f"received username from client: {username}")
    except (KeyError, ValueError):
        return "", "", upstream_request_headers

    username, addressbook = split_username(username)

    credentials = b64encode(f"{username}:{password}".encode()).decode()
    upstream_request_headers["authorization"] = f"{authorization_type} {credentials}"

    return username, addressbook, upstream_request_headers
