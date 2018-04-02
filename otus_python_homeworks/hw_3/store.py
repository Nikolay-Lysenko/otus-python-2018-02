import time
from contextlib import contextmanager

from pymemcache.client import base as memcache_base


@contextmanager
def connect_in_hammer_mode(store, sleep_time=1, sleep_factor=1):
    # type: (InMemoryStorage, int, int) -> ...
    """
    Try to connect several times. Always close open connections.
    """
    for i in xrange(store.max_n_attempts):
        try:
            conn = store.get_conn()
            yield conn
        except:
            time.sleep((1 + sleep_factor*i) * sleep_time)
            continue
        else:
            break
        finally:
            conn.close()


class InMemoryStorage(object):
    """
    This class provides specified in the homework description API to
    in-memory NoSQL database `memcached`.
    """

    def __init__(
            self, host=None, port=None, timeout=None, max_n_attempts=None
            ):
        # type: (str, int, int) -> type(None)
        self.host = host or "127.0.0.1"
        self.port = port or 11211
        self.timeout = timeout or 60
        self.max_n_attempts = max_n_attempts or 3

    def get_conn(self):
        """
        Try to establish connection.
        """
        conn = memcache_base.Client(
            server=(self.host, self.port),
            connect_timeout=self.timeout,
            timeout=self.timeout
        )
        return conn

    def cache_set(self, key, value, expire=None):
        # type: (str, Any, int) -> type(None)
        """
        Set casted to string value to cache for a specified
        amount of seconds.
        """
        with connect_in_hammer_mode(self) as conn:
            conn.set(key, str(value), expire)

    def cache_get(self, key):
        # type: (str) -> str
        """
        Get cached value.
        """
        with connect_in_hammer_mode(self) as conn:
            return conn.get(key)

    def get(self, key):
        # type: (str) -> str
        """
        Get value from a sort of DB which is actually in-memory cache.
        """
        return self.cache_get(key)
