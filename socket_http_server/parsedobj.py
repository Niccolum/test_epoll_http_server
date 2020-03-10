from io import BytesIO
from typing import Tuple, Dict, Union
from http import HTTPStatus
import datetime as dt
import mimetypes
from pathlib import Path
import urllib.parse as parse


def parse_raw_request(raw_request: bytes) -> Tuple[Dict[str, Union[str, Dict[str, str]]], Dict[str, str]]:
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


def response_to_raw(headers: dict, status_code: int, proto: str) -> bytes:
    status = next(st for st in list(HTTPStatus) if st.value == status_code)
    first_line = f"{proto} {status.value} {status.phrase}\r\n"
    raw_headers = '\r\n'.join(f'{k}: {v}' for k, v in headers.items()) + '\r\n\r\n'
    bytes_response = f"{first_line}{raw_headers}".encode()
    return bytes_response


def _get_file_lenght(fp: BytesIO) -> int:
    fp.seek(0, 2)
    size = fp.tell()
    fp.seek(0)
    return size


def _create_response_headers(body: BytesIO, url: str) -> Dict[str, str]:
    content_type, _ = mimetypes.guess_type(url)
    return {
        'Date': dt.datetime.now().isoformat(),
        'Content-Type': content_type,
        'Content-Length': _get_file_lenght(body),
        'Server': 'Niccolum_simpleHTTP_webserver',
        'Connection': 'close',
    }


def create_response(status: int, body: BytesIO, url) -> Dict[str, Union[int, BytesIO, Dict[str, str]]]:
    headers = _create_response_headers(body, url)
    response_dict = {
        'headers': headers,
        'body': body,
        'status_code': status
    }
    return response_dict


def parse_url(raw_url):
    quote_path = parse.urlparse(raw_url).path
    path = parse.unquote(quote_path)

    if path.endswith('/'):
        path += 'index.html'

    path = path.lstrip('/')
    return path


def status_body_by_path(directory: Path, raw_url: str):
    path = parse_url(raw_url)

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
