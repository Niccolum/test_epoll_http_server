import socket
from io import BytesIO
from typing import Optional, Iterable, Generator
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
    body: BytesIO
    status_code: int
    raw: Optional[Iterable[BytesIO]] = None

    def __post_init__(self) -> None:
        self.chunks_processing = self._read_from_chunks()
        self._chunks_cursor = 0

    def create_raw(self, request: Request) -> None:
        resp_headers_bytes = BytesIO(response_to_raw(self.headers, self.status_code, request.proto))
        self.raw = (resp_headers_bytes, self.body)

    def _read_from_chunks(self, chunk_size: int = 1024) -> Generator[bytes, None, None]:
        for byte_io_object in self.raw:
            while True:
                byte_io_object.seek(self._chunks_cursor)
                data = byte_io_object.read(chunk_size)
                byte_io_object.seek(self._chunks_cursor)
                if not data:
                    break
                yield data
            self.chunks_cursor = 0


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
            status = HTTPStatus.BAD_REQUEST.value
            body = BytesIO(error['message'].encode())
        elif self.request.method not in ('GET', 'HEAD'):
            status = HTTPStatus.METHOD_NOT_ALLOWED.value
            body = BytesIO(HTTPStatus.METHOD_NOT_ALLOWED.description.encode())
        else:
            status, body = status_body_by_path(directory, self.request.path)

        response = create_response(status=status, body=body, url=self.request.path)

        if self.request.method == 'HEAD':
            response['body'] = BytesIO(b'')

        parsed_response = Response(**response)
        parsed_response.create_raw(self.request)
        self.response = parsed_response
