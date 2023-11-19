import logging

from flask import request
from lxml import etree

from app import app
from helpers import (
    log_downstream_request,
    process_authorization_header,
)
from interaction import make_downstream_response, proxy_to_upstream

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


def setup_routes():
    pass
