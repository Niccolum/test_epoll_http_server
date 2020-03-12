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

    def _create_server(self) -> None:
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # We allow bind () to be executed on line 11 even if another program recently listened to the same port.
        # Without this, the program will not be able to work with the port for 1-2 minutes
        # after finishing work with the same port in a previously launched program.
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind(('0.0.0.0', self.port))
        # We tell the server socket to start accepting incoming connections from clients.
        _clients_queue = 50
        self.server_socket.listen(_clients_queue)

    def __enter__(self) -> HTTPServer:
        self._create_server()
        return self

    def __exit__(self, type_, val, traceback) -> None:
        self.server_socket.close()

    def _run(self) -> None:
        runner = ServerWorker(server_socket=self.server_socket, base_directory=self.base_directory)
        runner()

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


class ServerWorker:

    def __init__(self, server_socket, base_directory):
        self.server_socket = server_socket
        self.base_directory = base_directory
        self.epoll = select.epoll()
        # We subscribe to read events on the server socket.
        # The read event occurs when the server socket accepts the connection.
        self.epoll.register(self.server_socket.fileno(), select.EPOLLIN)
        self.connections: Dict[int, Connection] = {}

    def __call__(self):
        try:
            while True:
                self._run_loop()
        finally:
            while self.connections:
                self._run_loop(graceful_shutdown=True)
            self.epoll.unregister(self.server_socket.fileno())
            self.epoll.close()

    def _register_new_connection(self) -> None:
        curr_conn, _ = self.server_socket.accept()
        curr_conn.setblocking(False)
        # Subscribing to read events (EPOLLIN) on a new socket.
        self.epoll.register(curr_conn.fileno(), select.EPOLLIN)
        self.connections[curr_conn.fileno()] = Connection(client=curr_conn)

    def _read_new_data_for_connection(self, fileno: int):
        curr_conn = self.connections[fileno]
        curr_conn.raw_request += curr_conn.client.recv(1024)
        if any(eol in curr_conn.raw_request for eol in EOL):
            curr_conn.parse_request(self.base_directory)
            self.epoll.modify(fileno, select.EPOLLOUT)

    def _write_data_for_request(self, fileno: int):
        curr_conn = self.connections[fileno]
        chunk = next(curr_conn.response.chunks_processing, None)
        if chunk:
            bytes_written = curr_conn.client.send(chunk)
            curr_conn.response.chunks_cursor += bytes_written
        else:
            self.epoll.modify(fileno, select.EPOLLHUP)
            curr_conn.client.shutdown(socket.SHUT_RDWR)

    def _close_request(self, fileno: int):
        self.epoll.unregister(fileno)
        self.connections[fileno].client.close()
        del self.connections[fileno]

    def _run_loop(self, graceful_shutdown: bool = False):
        events = self.epoll.poll(1)
        for fileno, event in events:
            # if new socket session
            if not graceful_shutdown and fileno == self.server_socket.fileno():
                self._register_new_connection()
            # Available for read
            elif event & select.EPOLLIN:
                self._read_new_data_for_connection(fileno)
            # Available for write
            elif event & select.EPOLLOUT:
                self._write_data_for_request(fileno)
            # Available for close
            elif event & select.EPOLLHUP:
                self._close_request(fileno)
