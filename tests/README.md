# Comments for tests

## HW 1
Log files should be located at `tests/hw_1/log` directory. Test assumes that the file `nginx-access-ui.20170630.gz` is there. This file is not included into the repository, because it is not a good practice to store binary files in Git repositories.

## HW 3
Before running the tests, `redis` should be launched. To download a Docker image of it, run below command from a terminal:
```
docker pull library/redis
```

To launch a Docker container and to redirect its port to your `localhost`, run this:
```
docker run -d -p 6379:6379 redis
```
