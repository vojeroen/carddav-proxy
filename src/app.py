import gzip
import logging
import os
from base64 import b64decode, b64encode
from logging.config import dictConfig
from urllib.parse import urljoin

import requests
from flask import Flask, make_response
from flask import request
from lxml import etree

LOG_LEVEL = os.environ.get("LOG_LEVEL", "DEBUG").upper()
UPSTREAM_SERVER = os.environ.get("UPSTREAM_SERVER")
THIS_SERVER = os.environ.get("THIS_SERVER")
STRIP_HEADERS_TO_UPSTREAM = "host"
STRIP_HEADERS_FROM_UPSTREAM = "transfer-encoding", "content-encoding"

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
logger = logging.getLogger(__name__)

HTTP_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]
WEBDAV_METHODS = [
    "PROPFIND",
    "PROPPATCH",
    "MKCOL",
    "COPY",
    "MOVE",
    "LOCK",
    "UNLOCK",
    "REPORT",
]


def make_downstream_response(content, status_code, headers):
    logger.debug(f"downstream response status code: {status_code}")
    logger.debug(f"downstream response content: {content}")
    logger.debug(f"downstream response headers: {headers}")

    try:
        headers["location"] = headers["location"].replace(UPSTREAM_SERVER, THIS_SERVER)
    except KeyError:
        pass

    headers = [
        (k, v)
        for k, v in headers.items()
        if k.lower() not in STRIP_HEADERS_FROM_UPSTREAM
    ]

    if "gzip" in request.headers.get("accept-encoding", ""):
        headers += [("content-encoding", "gzip")]
        content = gzip.compress(content)

    return make_response(
        (
            content,
            status_code,
            headers,
        )
    )


def proxy_to_upstream(method, route, content, headers):
    logger.debug(f"upstream request method: {method}")
    logger.debug(f"upstream request route: {route}")
    logger.debug(f"upstream request content: {content}")
    logger.debug(f"upstream request headers: {headers}")

    headers = {
        k: v for k, v in headers.items() if k.lower() not in STRIP_HEADERS_TO_UPSTREAM
    }

    upstream_response = requests.request(
        method=method,
        url=urljoin(UPSTREAM_SERVER, route),
        data=content,
        headers=headers,
        allow_redirects=False,
    )

    logger.debug(f"upstream response status code: {upstream_response.status_code}")
    logger.debug(f"upstream response content: {upstream_response.content}")
    logger.debug(f"upstream response headers: {upstream_response.headers}")

    return upstream_response


def split_username(username):
    try:
        username, addressbook = username.split("#")
    except ValueError:
        addressbook = None
    return username, addressbook


def log_downstream_request():
    logger.debug(f"downstream request method: {request.method}")
    logger.debug(f"downstream request content: {request.data}")
    logger.debug(f"downstream request headers: {request.headers}")
    logger.debug(f"downstream request cookies: {request.cookies}")


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


@app.route(
    "/remote.php/dav/addressbooks/users/<string:path_username>/",
    methods=["PROPFIND"],
)
def address_book_listing(path_username):
    logger.debug("invoking address book listing")
    log_downstream_request()

    username, addressbook, upstream_request_headers = process_authorization_header()

    if username:
        route = f"/remote.php/dav/addressbooks/users/{username}/"
    else:
        route = f"/remote.php/dav/addressbooks/users/{path_username}/"

    upstream_response = proxy_to_upstream(
        method=request.method,
        route=route,
        content=request.data,
        headers=upstream_request_headers,
    )

    if addressbook is None:
        downstream_response_content = upstream_response.content
    else:
        accepted_href = (route, f"{route}{addressbook}/")

        xml_response = etree.fromstring(upstream_response.content)
        for response_node in xml_response:
            href_nodes = response_node.xpath("d:href", namespaces=xml_response.nsmap)
            if len(href_nodes) != 1:
                return make_downstream_response(
                    content=upstream_response.content,
                    status_code=upstream_response.status_code,
                    headers=upstream_response.headers,
                )
            href_node = href_nodes[0]
            if href_node.text not in accepted_href:
                xml_response.remove(response_node)

        downstream_response_content = etree.tostring(
            xml_response, encoding=str
        ).encode()

    return make_downstream_response(
        content=downstream_response_content,
        status_code=upstream_response.status_code,
        headers=upstream_response.headers,
    )


@app.route("/", methods=HTTP_METHODS + WEBDAV_METHODS)
@app.route("/<path:route>", methods=HTTP_METHODS + WEBDAV_METHODS)
def main(route=""):
    logger.debug("invoking main")

    log_downstream_request()

    _, _, upstream_request_headers = process_authorization_header()

    upstream_response = proxy_to_upstream(
        method=request.method,
        route=route,
        content=request.data,
        headers=upstream_request_headers,
    )

    return make_downstream_response(
        content=upstream_response.content,
        status_code=upstream_response.status_code,
        headers=upstream_response.headers,
    )


if __name__ == "__main__":
    app.run()
