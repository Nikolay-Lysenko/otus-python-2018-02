# Comments for tests

## HW 1
Log files should be located at `tests/hw_1/log` directory. Test assumes that the file `nginx-access-ui.20170630.gz` is there.
Script `tests/hw_1/test_log_analyzer.py` successfully terminates if it is launched from its directory, i.e., the command `python test_log_analyzer.py` is used.

## HW 3
Before running the tests, `redis` should be launched. To download a Docker image of it, run below command from a terminal:
```
docker pull library/redis
```

To launch a Docker container and to redirect its port to your `localhost`, run this:
```
docker run -d -p 6379:6379 redis
```
