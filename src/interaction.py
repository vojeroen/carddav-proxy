import gzip
import logging
from urllib.parse import urljoin

import requests
from flask import request, make_response

from settings import (
    UPSTREAM_SERVER,
    THIS_SERVER,
    STRIP_HEADERS_FROM_UPSTREAM,
    STRIP_HEADERS_TO_UPSTREAM,
)

logger = logging.getLogger(__name__)


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
