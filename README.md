# Test socket epoll http server

Here is example of realization asynchronous http web server on epoll (select.epoll) on sockets

## Getting Started

### Requirements

Python 3.7+

* Respond to `GET` with status code in `{200,403,404}`
* Respond to `HEAD` with status code in `{200,403,404}`
* Respond to all other request methods with status code `405`
* Directory index file name `index.html`
* Respond to requests for `/<file>.html` with the contents of `DOCUMENT_ROOT/<file>.html`
* Requests for `/<directory>/` should be interpreted as requests for `DOCUMENT_ROOT/<directory>/index.html`
* Respond with the following header fields for all requests:
  * `Server`
  * `Date`
  * `Connection`
  * `Content-Length`
  * `Content-Type`
* Respond with correct `Content-Type` for `.html, .css, js, jpg, .jpeg, .png, .gif, .swf`
* Respond to percent-encoding URLs
* No security vulnerabilities!

### Installing

```bash
$ git clone git@github.com:Niccolum/test_epoll_http_server.git
```

### Run

#### Console

```bash
$ cd /path/to/root/dir

$ python3.7 httpd.py --help
usage: httpd.py [-h] [-w W] [-r R]

optional arguments:
  -h, --help  show this help message and exit
  -w W        Number of workers. Default 4
  -r R        Documents root. Default current directory


$ python3.7 httpd.py -w 4
```

#### Docker

```bash
$ cd /path/to/root/dir

$ docker image build -t niccolum_socket_http_server:1.0 .
$ docker container run --publish 8080:8080 --detach --name nshs niccolum_socket_http_server:1.0
```

### Unit Testing

After running server enter the following command:

```bash
$ python3.7 httptest.py
```

### Stress Testing

After running server enter the following command:

#### 1 worker

```bash
$ ab -n 50000 -c 100 -r http://localhost:8080/
This is ApacheBench, Version 2.3 <$Revision: 1807734 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking localhost (be patient)
Completed 5000 requests
Completed 10000 requests
Completed 15000 requests
Completed 20000 requests
Completed 25000 requests
Completed 30000 requests
Completed 35000 requests
Completed 40000 requests
Completed 45000 requests
Completed 50000 requests
Finished 50000 requests


Server Software:        Niccolum_simpleHTTP_webserver
Server Hostname:        localhost
Server Port:            8080

Document Path:          /
Document Length:        29 bytes

Concurrency Level:      100
Time taken for tests:   9.727 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      50000
Total transferred:      9350000 bytes
HTML transferred:       1450000 bytes
Requests per second:    5140.11 [#/sec] (mean)
Time per request:       19.455 [ms] (mean)
Time per request:       0.195 [ms] (mean, across all concurrent requests)
Transfer rate:          938.67 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    3  97.9      0    3043
Processing:     3   15 186.7     10    6653
Waiting:        3   15 186.7     10    6653
Total:          4   19 278.0     10    9695

Percentage of the requests served within a certain time (ms)
  50%     10
  66%     11
  75%     11
  80%     11
  90%     11
  95%     13
  98%     13
  99%     15
 100%   9695 (longest request)
```

#### 4 workers

```bash
$ ab -n 50000 -c 100 -r http://localhost:8080/
This is ApacheBench, Version 2.3 <$Revision: 1807734 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking localhost (be patient)
Completed 5000 requests
Completed 10000 requests
Completed 15000 requests
Completed 20000 requests
Completed 25000 requests
Completed 30000 requests
Completed 35000 requests
Completed 40000 requests
Completed 45000 requests
Completed 50000 requests
Finished 50000 requests


Server Software:        Niccolum_simpleHTTP_webserver
Server Hostname:        localhost
Server Port:            8080

Document Path:          /
Document Length:        29 bytes

Concurrency Level:      100
Time taken for tests:   4.836 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      50000
Total transferred:      9349993 bytes
HTML transferred:       1450000 bytes
Requests per second:    10340.00 [#/sec] (mean)
Time per request:       9.671 [ms] (mean)
Time per request:       0.097 [ms] (mean, across all concurrent requests)
Transfer rate:          1888.26 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    4  58.3      0    1035
Processing:     0    5   8.9      5     421
Waiting:        0    5   8.9      5     421
Total:          0    9  63.7      5    1439

Percentage of the requests served within a certain time (ms)
  50%      5
  66%      6
  75%      6
  80%      7
  90%      8
  95%      9
  98%     11
  99%     15
 100%   1439 (longest request)
```

### PEP8
```bash
# create venv before

$ pip install flake8
$ cd /path/to/root/dir
$ flake8 --max-line-length=120 --exclude httptest.py
```