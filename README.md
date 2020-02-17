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

```bash
$ cd /path/to/root/dir

$ python3.7 httpd.py --help
usage: httpd.py [-h] [-w W] [-r R]

optional arguments:
  -h, --help  show this help message and exit
  -w W        Number of workers. Default 4
  -r R        Documents root. Default current directory


$ python3.7 httpd.py
```


### Unit Testing

After running server enter the following command:

```bash
$ python3.7 httptest.py
```

### Stress Testing

After running server enter the following command:

```bash
$ ab ‐n 50000 ‐c 100 -r http://localhost:8080/
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
Time taken for tests:   7.790 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      50000
Total transferred:      9650000 bytes
HTML transferred:       1450000 bytes
Requests per second:    6418.61 [#/sec] (mean)
Time per request:       15.580 [ms] (mean)
Time per request:       0.156 [ms] (mean, across all concurrent requests)
Transfer rate:          1209.76 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    1  41.6      0    3040
Processing:     3   14 187.1      8    6735
Waiting:        3   14 187.1      8    6735
Total:          7   15 219.0      8    7750

Percentage of the requests served within a certain time (ms)
  50%      8
  66%      9
  75%      9
  80%      9
  90%      9
  95%      9
  98%     10
  99%     11
 100%   7750 (longest request)

```