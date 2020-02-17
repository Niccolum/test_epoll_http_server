import argparse
from pathlib import Path

from socket_http_server.core import HTTPServer

BASE_DIR = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-w", type=int, default=1, help="Number of workers. Default 1")
    parser.add_argument("-r", type=str, default='/', help="Documents root. Default current directory")
    args = parser.parse_args()

    doc_root = args.r.lstrip('/')
    directory = BASE_DIR / doc_root

    app = HTTPServer(base_directory=directory, port=8080, processes=args.w)
    try:
        print('Starting server, use <Ctrl-C> to stop')
        app.run()
    except KeyboardInterrupt:
        print('Server has been stopped')


if __name__ == '__main__':
    main()
