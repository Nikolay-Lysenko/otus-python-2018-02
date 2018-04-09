## Simple HTTP Server Wriiten at Socket-Level

#### Architecture

There are several processes that listen a specified port and every connection is handled in a separate thread within one of the processes.

#### Launch

Run `python httpd.py -h` to see possible options.

#### Load testing

The command `wrk -t12 -c400 -d30s http://127.0.0.1:8080/httptest/dir2/` produced the following results:

```
Running 30s test @ http://127.0.0.1:8080/httptest/dir2/
  12 threads and 400 connections
  Thread Stats   Avg      Stdev     Max   +/- Stdev
    Latency    26.48ms  118.27ms   1.97s    94.98%
    Req/Sec   181.69    177.39     1.91k    93.31%
  59408 requests in 30.08s, 10.20MB read
  Socket errors: connect 0, read 0, write 0, timeout 62
Requests/sec:   1974.88
Transfer/sec:    347.15KB
```
