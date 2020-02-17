from io import BytesIO
from typing import Tuple, Dict, Union
from http import HTTPStatus
import datetime as dt
import mimetypes
from pathlib import Path
import urllib.parse as parse

MIMETYPES = mimetypes.types_map
MIMETYPES['default'] = 'text/plain'

# MIMETYPES = {
#     'default': 'text/plain',
#     '.html': 'text/html',
#     '.css': 'text/css',
#     '.js': 'application/javascript',
#     '.jpg': 'image/jpeg',
#     '.jpeg': 'image/jpeg',
#     '.png': 'image/png',
#     '.gif': 'image/gif',
#     '.swf': 'application/x-shockwave-flash',
# }


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


def response_to_raw(headers: dict, body: bytes, status_code: int, proto: str) -> bytes:
    status = next(st for st in list(HTTPStatus) if st.value == status_code)
    first_line = f"{proto} {status.value} {status.phrase}\r\n"
    raw_headers = '\r\n'.join(f'{k}: {v}' for k, v in headers.items()) + '\r\n\r\n'
    bytes_response = f"{first_line}{raw_headers}".encode()
    bytes_response += body
    return bytes_response


def _create_response_headers(body: bytes, content_type: str) -> Dict[str, str]:
    return {
        'Date': dt.datetime.now().isoformat(),
        'Content-Type': MIMETYPES[content_type],
        'Content-Length': len(body),
        'Server': 'Niccolum_simpleHTTP_webserver',
        'Connection': 'close',
    }


def create_response(status: int, body: bytes, content_type: str='default') -> Dict[str, Union[str, Dict[str, str]]]:
    headers = _create_response_headers(body, content_type)
    response_dict = {
        'headers': headers,
        'body': body,
        'status_code': status
    }
    return response_dict


def status_body_by_path(directory: Path, raw_path: str):
    quote_path = parse.urlparse(raw_path).path
    path = parse.unquote(quote_path)

    if path.endswith('/'):
        path += 'index.html'

    path = path.lstrip('/')

    full_path = (directory / path).resolve()
    content_type = 'default'

    if full_path.exists():
        try:
            full_path.relative_to(directory)
            body = full_path.open(mode='rb').read()
            status = HTTPStatus.OK.value
            content_type = full_path.suffix or content_type
        except (PermissionError, ValueError):
            body = HTTPStatus.FORBIDDEN.description.encode()
            status = HTTPStatus.FORBIDDEN.value
    else:
        body = HTTPStatus.NOT_FOUND.description.encode()
        status = HTTPStatus.NOT_FOUND.value

    return status, body, content_type
