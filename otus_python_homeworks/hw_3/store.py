import time

import redis


def execute_in_hammer_mode(func):
    """
    A decorator for automation of reconnecting.
    """
    n_trials = 3
    sleep_time = 1
    sleep_factor = 1

    def wrapper(*args, **kwargs):
        for i in range(n_trials):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if i == n_trials - 1:
                    raise RuntimeError(e)
                else:
                    time.sleep((1 + sleep_factor * i) * sleep_time)
                    # `args[0]` is an instance of `InMemoryStorage`
                    args[0].close_connection()
                    args[0].connect()
                    continue
    return wrapper


class InMemoryStorage(object):
    """
    This class provides specified in the homework description API to
    in-memory NoSQL database `redis`.
    """

    def __init__(
            self, host=None, port=None, timeout=None
            ):
        # type: (str, int, int) -> type(None)
        self.host = host or "127.0.0.1"
        self.port = port or 6379
        self.timeout = timeout or 60
        self.connection = None
        self.connect()

    def connect(self):
        """
        Try to establish connection.
        """
        self.connection = redis.Redis(
            host=self.host,
            port=self.port,
            socket_connect_timeout=self.timeout,
            socket_timeout=self.timeout
        )

    def close_connection(self):
        """
        Close open connection.
        """
        self.connection = None

    @execute_in_hammer_mode
    def __cache_set(self, key, value, expire):
        # type: (str, Any, int) -> type(None)
        # Implement internal logic for `cache_set` method.
        self.connection.set(key, str(value), expire)

    @execute_in_hammer_mode
    def __cache_get(self, key):
        # type: (str) -> Optional[str]
        # Implement internal logic for `cache_set` method.
        return self.connection.get(key)

    def cache_set(self, key, value, expire=None):
        # type: (str, Any, int) -> type(None)
        """
        Insert casted to string value into cache for a specified
        amount of seconds.
        """
        try:
            self.__cache_set(key, value, expire)
        except RuntimeError:
            pass

    def cache_get(self, key):
        # type: (str) -> Optional[str]
        """
        Get cached value.
        """
        try:
            return self.__cache_get(key)
        except RuntimeError:
            return None

    def get(self, key):
        # type: (str) -> str
        """
        Get value from a sort of DB which is actually in-memory cache.
        """
        return self.__cache_get(key)
