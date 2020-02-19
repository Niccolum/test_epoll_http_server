# Test socket epoll http server

Here is example of realization asynchronous http web server on epoll (select.epoll) on sockets

## Getting Started

### Requirements

Python 3.7+

* Respond to `GET` with status code in `{200,403,404}`
* Respond to `HEAD` with status code in `{200,404}`
* Respond to all other request methods with status code `405`
* Directory index file name `index.html`
* Respond to requests for `/<file>.html` with the contents of `DOCUMENT_ROOT/<file>.html`
* Requests for `/<directory>/` should be interpreted as requests for `DOCUMENT_ROOT/<directory>/index.html`
* Respond with the following header fields for all requests:
  * `Server`
  * `Date`
  * `Connection`
* Respond with the following additional header fields for all `200` responses to `GET` and `HEAD` requests:
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
Time taken for tests:   14.401 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      50000
Total transferred:      9650000 bytes
HTML transferred:       1450000 bytes
Requests per second:    3472.10 [#/sec] (mean)
Time per request:       28.801 [ms] (mean)
Time per request:       0.288 [ms] (mean, across all concurrent requests)
Transfer rate:          654.41 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    2  65.5      0    3040
Processing:     4   12 174.7      8   13344
Waiting:        4   12 174.7      8   13344
Total:          6   14 227.8      8   14363

Percentage of the requests served within a certain time (ms)
  50%      8
  66%      9
  75%      9
  80%      9
  90%     10
  95%     11
  98%     13
  99%     15
 100%  14363 (longest request)
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
Time taken for tests:   5.160 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      50000
Total transferred:      9650000 bytes
HTML transferred:       1450000 bytes
Requests per second:    9690.28 [#/sec] (mean)
Time per request:       10.320 [ms] (mean)
Time per request:       0.103 [ms] (mean, across all concurrent requests)
Transfer rate:          1826.39 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    4  58.9      0    1033
Processing:     0    5   4.5      5     579
Waiting:        0    5   4.4      4     579
Total:          0    9  59.7      5    1239

Percentage of the requests served within a certain time (ms)
  50%      5
  66%      6
  75%      6
  80%      7
  90%      8
  95%     10
  98%     13
  99%     17
 100%   1239 (longest request)
```