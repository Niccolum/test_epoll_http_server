# Test socket epoll http server

Here is example of realization http web server on epoll (select.epoll) on sockets

## Getting Started

### Requirements

Python 3.6+

### Installing

```bash
git clone git@github.com:Niccolum/test_epoll_http_server.git
```

### Run

```bash
cd /path/to/root/dir
python3 httpd.py
```

### Testing

```bash
ab ‐n 50000 ‐c 100 -r http://localhost:8080/
```