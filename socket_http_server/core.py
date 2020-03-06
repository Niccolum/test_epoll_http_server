from __future__ import annotations
import socket
import select
from typing import Dict
from pathlib import Path
import multiprocessing as mp

from socket_http_server.structures import Connection


EOL = (b'\n\n', b'\n\r\n')


class HTTPServer:
    def __init__(self, base_directory='/', port=8080, processes=1) -> None:
        self.port = port
        self.base_directory = Path(__file__).resolve() / base_directory
        self.processes = processes
        self.server_socket = None
        self.epoll = None

    def _create_server(self) -> None:
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # Разрешаем выполнять bind() в строке 11 даже в случае, если другая программа недавно слушала тот же порт.
        # Без этого, программа не сможет работать с портом в течение 1-2 минут
        # после окончания работы с тем же портом в ранее запущенной программе.
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.port))
        # Указываем серверному сокету начать прием входящих соединений от клиентов.
        _clients_queue = 50
        self.server_socket.listen(_clients_queue)

    def __enter__(self) -> HTTPServer:
        self._create_server()
        return self

    def __exit__(self, type, val, traceback) -> None:
        self.server_socket.close()

    def _register_new_connection(self, epoll: select.epoll, _connections: Dict[int, Connection]) -> None:
        curr_conn, _ = self.server_socket.accept()
        curr_conn.setblocking(False)
        # Подписываемся на события чтения (EPOLLIN) на новом сокете.
        epoll.register(curr_conn.fileno(), select.EPOLLIN)
        _connections[curr_conn.fileno()] = Connection(client=curr_conn)

    def _read_new_data_for_connection(self, fileno: int, epoll: select.epoll, _connections: Dict[int, Connection]):
        curr_conn = _connections[fileno]
        curr_conn.raw_request += curr_conn.client.recv(1024)
        if any(eol in curr_conn.raw_request for eol in EOL):
            curr_conn.parse_request(self.base_directory)
            epoll.modify(fileno, select.EPOLLOUT)

    def _write_data_for_request(self, fileno: int, epoll: select.epoll, _connections: Dict[int, Connection]):
        curr_conn = _connections[fileno]

        chunk = next(curr_conn.response.chunks, None)

        if chunk:
            curr_conn.client.send(chunk)
        else:
            epoll.modify(fileno, select.EPOLLHUP)
            curr_conn.client.shutdown(socket.SHUT_RDWR)

    def _close_request(self, fileno: int, epoll: select.epoll, _connections: Dict[int, Connection]):
        epoll.unregister(fileno)
        _connections[fileno].client.close()
        del _connections[fileno]

    def _run_loop(self, epoll: select.epoll, _connections: Dict[int, Connection], graceful_shutdown: bool=False):
        events = epoll.poll(1)
        for fileno, event in events:
            # if new socket session
            if not graceful_shutdown and fileno == self.server_socket.fileno():
                self._register_new_connection(epoll, _connections)
            # Available for read
            elif event & select.EPOLLIN:
                self._read_new_data_for_connection(fileno, epoll, _connections)
            # Available for write
            elif event & select.EPOLLOUT:
                self._write_data_for_request(fileno, epoll, _connections)
            # Available for close
            elif event & select.EPOLLHUP:
                self._close_request(fileno, epoll, _connections)

    def _run(self) -> None:
        epoll = select.epoll()
        # Подписываемся на события чтения на серверном сокете.
        # Событие чтения происходит в тот момент, когда серверный сокет принимает подключение.
        epoll.register(self.server_socket.fileno(), select.EPOLLIN)
        _connections = {}
        try:
            while True:
                self._run_loop(epoll=epoll, _connections=_connections)
        finally:
            while _connections:
                self._run_loop(epoll=epoll, _connections=_connections, graceful_shutdown=True)
            epoll.unregister(self.server_socket.fileno())
            epoll.close()

    def run(self) -> None:
        workers = [mp.Process(target=self._run) for _ in range(self.processes)]
        try:
            for p in workers:
                p.daemon = True
                p.start()
                print(f'Worker {p.name} are ready...')

            for p in workers:
                p.join()

        finally:
            for p in workers:
                p.terminate()
                print(f'Worker {p.name} has been stopped.')
