import gzip
import logging
from urllib.parse import urljoin

import requests
from requests.utils import dict_from_cookiejar
from flask import request, make_response

from settings import (
    UPSTREAM_SERVER,
    THIS_SERVER,
    STRIP_HEADERS_FROM_UPSTREAM,
    STRIP_HEADERS_TO_UPSTREAM,
)

logger = logging.getLogger(__name__)


def proxy_to_upstream(method, route, content, headers, cookies):
    logger.debug(f"upstream request method: {method}")
    logger.debug(f"upstream request route: {route}")
    logger.debug(f"upstream request content: {content}")
    logger.debug(f"upstream request headers: {headers}")
    logger.debug(f"upstream request cookies: {cookies}")

    headers = {
        k: v for k, v in headers.items() if k.lower() not in STRIP_HEADERS_TO_UPSTREAM
    }

    upstream_response = requests.request(
        method=method,
        url=urljoin(UPSTREAM_SERVER, route),
        data=content,
        headers=headers,
        cookies=cookies,
        allow_redirects=False,
    )

    logger.debug(f"upstream response status code: {upstream_response.status_code}")
    logger.debug(f"upstream response content: {upstream_response.content}")
    logger.debug(f"upstream response headers: {upstream_response.headers}")
    logger.debug(f"upstream response cookies: {upstream_response.cookies}")

    return upstream_response


def make_downstream_response(content, status_code, headers, cookies, addressbook=None):
    logger.debug(f"downstream response status code: {status_code}")
    logger.debug(f"downstream response content: {content}")
    logger.debug(f"downstream response headers: {headers}")
    logger.debug(f"downstream response cookies: {cookies}")
    logger.debug(f"downstream response set addressbook cookie: {addressbook}")

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

    response = make_response(
        (
            content,
            status_code,
            headers,
        )
    )

    for k, v in dict_from_cookiejar(cookies).items():
        response.set_cookie(k, v)

    if addressbook:
        response.set_cookie("carddav_proxy_addressbook", addressbook)

    return response
