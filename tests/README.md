# Comments for tests

## HW 1
Log files should be located at `tests/hw_1/log` directory. Test assumes that the file `nginx-access-ui.20170630.gz` is there.
Script `tests/hw_1/test_log_analyzer.py` successfully terminates if it is launched from its directory, i.e., the command `python test_log_analyzer.py` is used.

## HW 3
Before running the script, `memcached` should be started. If it is installed, one can just type `memcached` from a terminal. The command for running tests is:
```
cd tests/hw_3
python test.py
```
