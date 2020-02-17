import socket
from typing import Optional
from dataclasses import dataclass, field
from pathlib import Path
from http import HTTPStatus

from socket_http_server.parsedobj import (
    parse_raw_request,
    create_response,
    response_to_raw,
    status_body_by_path
)


@dataclass
class Request:
    method: str
    headers: field(default_factory=dict)
    path: str
    proto: str


@dataclass
class Response:
    headers: field(default_factory=dict)
    body: bytes
    status_code: int
    raw: bytes = b''

    def create_raw(self, request: Request):
        resp_bytes = response_to_raw(self.headers, self.body, self.status_code, request.proto)
        self.raw = resp_bytes


@dataclass
class Connection:
    client: socket.socket
    raw_request: bytes = b''
    request: Optional[Request] = None
    response: Optional[Response] = None

    def parse_request(self, directory: Path):
        error, request = parse_raw_request(self.raw_request)
        self.request = Request(**request)
        if error['code']:
            response = create_response(status=HTTPStatus.BAD_REQUEST.value, body=error['message'].encode())
        elif self.request.method not in ('GET', 'HEAD'):
            response = create_response(
                status=HTTPStatus.METHOD_NOT_ALLOWED.value, body=HTTPStatus.METHOD_NOT_ALLOWED.description.encode())
        else:
            status, body, content_type = status_body_by_path(directory, self.request.path)
            response = create_response(status=status, body=body, content_type=content_type)

        if self.request.method == 'HEAD':
            response['body'] = b''
        parsed_response = Response(**response)
        parsed_response.create_raw(self.request)
        self.response = parsed_response
