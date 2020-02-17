import socket
import select
from typing import Tuple
from pathlib import Path
import multiprocessing as mp

from socket_http_server.structures import Connection

class HTTPServer:
    def __init__(self, base_directory='/', port=8080, processes=1) -> None:
        self.port = port
        self.base_directory = Path(__file__).resolve() / base_directory
        self.processes = processes
        self. manager = mp.Manager()
        self._connections = self.manager.dict()
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
        # Блокирующие по умолчанию сокеты нужно использовать в неблокирующем (асинхронном) режиме.
        self.server_socket.setblocking(False)
        self.epoll = select.epoll()
        # Подписываемся на события чтения на серверном сокете.
        # Событие чтения происходит в тот момент, когда серверный сокет принимает подключение.
        self.epoll.register(self.server_socket.fileno(), select.EPOLLIN)

    def __enter__(self) -> Tuple[socket.socket, select.epoll]:
        self._create_server()
        return self.server_socket, self.epoll

    def __exit__(self, type, val, traceback) -> None:
        self.epoll.unregister(self.server_socket.fileno())
        self.epoll.close()
        self.server_socket.close()


    def _register_new_connection(self) -> None:
        with mp.Lock():
            curr_conn, _ = self.server_socket.accept()
            curr_conn.setblocking(False)
            # Подписываемся на события чтения (EPOLLIN) на новом сокете.
            self.epoll.register(curr_conn.fileno(), select.EPOLLIN)
            self._connections[curr_conn.fileno()] = Connection(client=curr_conn)


    def _read_new_data_for_connection(self, fileno: int):
        eols = (b'\n\n', b'\n\r\n')
        curr_conn = self._connections[fileno]
        with mp.Lock():
            curr_conn.raw_request += curr_conn.client.recv(1024)
        if any(eol in curr_conn.raw_request for eol in eols):
            curr_conn.parse_request(self.base_directory)
            self.epoll.modify(fileno, select.EPOLLOUT)


    def _write_data_for_request(self, fileno: int):
        curr_conn = self._connections[fileno]
        bytes_written = curr_conn.client.send(curr_conn.response.raw)
        curr_conn.response.raw = curr_conn.response.raw[bytes_written:]
        if len(curr_conn.response.raw) == 0:
            self.epoll.modify(fileno, select.EPOLLHUP)
            curr_conn.client.shutdown(socket.SHUT_RDWR)


    def _close_request(self, fileno: int):
        self.epoll.unregister(fileno)
        self._connections[fileno].client.close()
        del self._connections[fileno]


    def _loop(self) -> None:
        while True:
            events = self.epoll.poll(1)
            for fileno, event in events:
                # if new socket session
                if fileno == self.server_socket.fileno():
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


    def run(self) -> None:
        with self:
            workers = [mp.Process(target=self._loop) for _ in range(self.processes)]
            for p in workers:
                p.daemon = True
                p.start()
                print(f'Worker {p.name} are ready...')

            for p in workers:
                p.join()
