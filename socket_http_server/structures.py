import socket
import mimetypes
import datetime as dt
from io import BytesIO
from typing import (
    Optional,
    Iterable,
    Generator,
    Tuple,
    Dict,
    Union,
)
from dataclasses import dataclass, field
from pathlib import Path
from http import HTTPStatus
import urllib.parse as parse


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
        self.chunks_cursor = 0

    def create_raw(self, request: Request) -> None:
        resp_headers_bytes = BytesIO(self._response_to_raw(request.proto))
        self.raw = (resp_headers_bytes, self.body)

    def _read_from_chunks(self, chunk_size: int = 1024) -> Generator[bytes, None, None]:
        for byte_io_object in self.raw:
            while True:
                byte_io_object.seek(self.chunks_cursor)
                data = byte_io_object.read(chunk_size)
                byte_io_object.seek(self.chunks_cursor)
                if not data:
                    byte_io_object.close()
                    break
                yield data
            self.chunks_cursor = 0

    def _response_to_raw(self, proto: str) -> bytes:
        status = next(st for st in list(HTTPStatus) if st.value == self.status_code)
        first_line = f"{proto} {status.value} {status.phrase}\r\n"
        raw_headers = '\r\n'.join(f'{k}: {v}' for k, v in self.headers.items()) + '\r\n\r\n'
        bytes_response = f"{first_line}{raw_headers}".encode()
        return bytes_response


@dataclass
class Connection:
    client: socket.socket
    raw_request: bytes = b''
    request: Optional[Request] = None
    response: Optional[Response] = None

    def parse_request(self, directory: Path):
        error, request = self._parse_raw_request(self.raw_request)
        self.request = Request(**request)
        if error['code']:
            status = HTTPStatus.BAD_REQUEST.value
            body = BytesIO(error['message'].encode())
        elif self.request.method not in ('GET', 'HEAD'):
            status = HTTPStatus.METHOD_NOT_ALLOWED.value
            body = BytesIO(HTTPStatus.METHOD_NOT_ALLOWED.description.encode())
        else:
            status, body = self._get_status_body_by_path(directory)

        response = self._create_response(status=status, body=body)

        if self.request.method == 'HEAD':
            response['body'] = BytesIO(b'')

        parsed_response = Response(**response)
        parsed_response.create_raw(self.request)
        self.response = parsed_response

    @staticmethod
    def _parse_raw_request(raw_request: bytes) -> Tuple[Dict[str, Union[str, Dict[str, str]]], Dict[str, str]]:
        headers = {}
        error_code = error_message = None
        method = path = proto = ''
        bfile = BytesIO(raw_request)
        try:
            first_line = bfile.readline().strip()
            method, path, proto = first_line.decode().split()
        except ValueError:
            error_code = 400
            error_message = 'Invalid request signature'
        else:
            try:
                line = bfile.readline().strip()
                while line:
                    key, value = line.decode().split(': ')
                    headers[key] = value
                    line = bfile.readline().strip()
            except ValueError:
                error_code = 400
                error_message = 'Invalid request signature'
        finally:
            parsed_request = {
                'method': method.upper(),
                'path': path,
                'proto': proto,
                'headers': headers,
            }
            error = {
                'code': error_code,
                'message': error_message
            }
            return error, parsed_request

    def _create_response(self, status: int, body: BytesIO) -> Dict[str, Union[int, BytesIO, Dict[str, str]]]:
        headers = self._create_response_headers(body)
        response_dict = {
            'headers': headers,
            'body': body,
            'status_code': status
        }
        return response_dict

    def _create_response_headers(self, body: BytesIO) -> Dict[str, str]:
        content_type, _ = mimetypes.guess_type(self.request.path)
        return {
            'Date': dt.datetime.now().isoformat(),
            'Content-Type': content_type,
            'Content-Length': self._get_file_lenght(body),
            'Server': 'Niccolum_simpleHTTP_webserver',
            'Connection': 'close',
        }

    @staticmethod
    def _get_file_lenght(fp: BytesIO) -> int:
        fp.seek(0, 2)
        size = fp.tell()
        fp.seek(0)
        return size

    @property
    def _path(self):
        quote_path = parse.urlparse(self.request.path).path
        path = parse.unquote(quote_path)

        if path.endswith('/'):
            path += 'index.html'

        path = path.lstrip('/')
        return path

    def _get_status_body_by_path(self, directory: Path):
        path = self._path

        full_path = (directory / path).resolve()

        if full_path.exists():
            try:
                full_path.relative_to(directory)
                body = full_path.open(mode='rb')
                status = HTTPStatus.OK.value
            except (PermissionError, ValueError):
                body = BytesIO(HTTPStatus.FORBIDDEN.description.encode())
                status = HTTPStatus.FORBIDDEN.value
        else:
            body = BytesIO(HTTPStatus.NOT_FOUND.description.encode())
            status = HTTPStatus.NOT_FOUND.value

        return status, body
