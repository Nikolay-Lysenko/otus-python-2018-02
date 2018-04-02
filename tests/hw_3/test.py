import unittest

from otus_python_homeworks.hw_3 import api, store


TOKEN = (
    "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954"
    "dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95"
)


def cases(requests):
    """
    A decorator for passing various test cases.
    """

    def nested_decorator(func):
        def wrapper(*args, **kwargs):
            for request in requests:
                func(request=request, *args, **kwargs)
        return wrapper

    return nested_decorator


class StorageMock(object):
    """
    Mock for `store.InMemoryStorage` class.
    """

    def __init__(self):
        self.kv = dict()

    def cache_set(self, key, value, expires=None):
        self.kv[key] = value

    def cache_get(self, key):
        return self.kv.get(key)

    def get(self, key):
        return self.kv.get(key)


# -----------------------------------------------------------------------------
# Unit tests.

# -----------------------------------------------------------------------------
# Functional tests.

class TestMethodHandler(unittest.TestCase):
    """
    Test `method_handler` function as well as functions and classes
    that are called by it.
    """

    def setUp(self):
        self.context = {}
        self.headers = {}
        self.storage = StorageMock()

    def get_response(self, request):
        """
        Internal convenience function.
        """
        return api.method_handler(
            {"body": request, "headers": self.headers},
            self.context, self.storage
        )

    def fill_storage(self, kv):
        """
        Internal convenience function.
        """
        for k, v in kv.items():
            self.storage.cache_set(k, v, 60*60)

    def test_empty_request(self):
        """
        Test that API correctly handles empty requests.
        """
        _, code = self.get_response({})
        self.assertEqual(api.INVALID_REQUEST, code)

    @cases([
        {
            "account": "horns&hoofs",
            "method": "online_score", "token": "sdd", "arguments": {}
        },
        {
            "account": "horns&hoofs", "login": "h&f",
            "token": "sdd", "arguments": {}
        },
        {
            "account": "horns&hoofs", "login": "admin",
            "method": "online_score", "arguments": {}
        },
        {
            "account": "horns&hoofs", "login": "admin",
            "method": "online_score", "token": "sdd"
        },
        {
            "account": "horns&hoofs", "login": "admin",
            "method": "online_score", "token": "sdd", "arguments": {},
            "extra_field": "gibberish"
        }
    ])
    def test_invalid_requests(self, request):
        """
        Test that API prohibits improperly structured requests.
        """
        _, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)

    @cases([
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "online_score", "token": "", "arguments": {}
        },
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "online_score", "token": "sdd", "arguments": {}
        },
        {
            "account": "horns&hoofs", "login": "admin",
            "method": "online_score", "token": "", "arguments": {}
        }
    ])
    def test_bad_auth(self, request):
        """
        Test that API forbids improperly authorized requests.
        """
        _, code = self.get_response(request)
        self.assertEqual(api.FORBIDDEN, code)

    @cases([
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "unknown", "token": TOKEN, "arguments": {}
        }
    ])
    def test_unknown_method(self, request):
        """
        Test that API fails gracefully in case of unknown method.
        """
        _, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)

    @cases([
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "online_score", "token": TOKEN,
            "arguments": {"email": 123}
        },
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "online_score", "token": TOKEN,
            "arguments": {"email": "me-at-otus.ru"}
        },
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "online_score", "token": TOKEN,
            "arguments": {"email": "me@otusru"}
        },
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "online_score", "token": TOKEN,
            "arguments": {"phone": {"country_code": 7, "number": 8002000600}}
        },
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "online_score", "token": TOKEN,
            "arguments": {"phone": 88002000600}
        },
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "online_score", "token": TOKEN,
            "arguments": {"phone": 7800200060}
        },
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "online_score", "token": TOKEN,
            "arguments": {"phone": 7800200060}
        },
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "online_score", "token": TOKEN,
            "arguments": {"first_name": 123}
        },
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "online_score", "token": TOKEN,
            "arguments": {"last_name": {"name": "John"}}
        },
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "online_score", "token": TOKEN,
            "arguments": {"birthday": "1990.01.01"}
        },
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "online_score", "token": TOKEN,
            "arguments": {"birthday": "01.01.1890"}
        },
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "online_score", "token": TOKEN,
            "arguments": {"gender": 3}
        },
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "online_score", "token": TOKEN,
            "arguments": {
                "first_name": "John",
                "email": "john.doe@example.com",
                "birthday": "01.01.1990"
            }
        },
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "clients_interests", "token": TOKEN,
            "arguments": {"date": "01.01.2018"}
        },
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "clients_interests", "token": TOKEN,
            "arguments": {"client_ids": {1: "+", 2: "-"}}
        },
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "clients_interests", "token": TOKEN,
            "arguments": {"client_ids": [1, 2, "3"]}
        },
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "clients_interests", "token": TOKEN,
            "arguments": {"client_ids": [1, 2, 3], "date": "2018.01.01"}
        }
    ])
    def test_invalid_arguments(self, request):
        """
        Test that API fails gracefully if improper arguments
        are passed.
        """
        _, code = self.get_response(request)
        self.assertEqual(api.BAD_REQUEST, code)

    @cases([
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "online_score", "token": TOKEN,
            "arguments": {"gender": 3, "extra_field": "gibberish"}
        },
        {
            "account": "horns&hoofs", "login": "h&f",
            "method": "clients_interests", "token": TOKEN,
            "arguments": {"client_ids": [1, 2], "extra_field": "gibberish"}
        }
    ])
    def test_extra_arguments(self, request):
        """
        Test that API fails gracefully if extra arguments
        are passed.
        """
        _, code = self.get_response(request)
        self.assertEqual(api.INVALID_REQUEST, code)

    def test_online_score_handler_with_all_arguments(self):
        """
        Test that API returns maximum score if all args are passed.
        """
        request = {
            "account": "horns&hoofs", "login": "h&f",
            "method": "online_score", "token": TOKEN,
            "arguments": {
                "phone": "79175002040", "email": "stupnikov@otus.ru",
                "first_name": "John", "last_name": "Doe",
                "birthday": "01.01.1990", "gender": 1
            }
        }
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code)
        self.assertEqual(5.0, response["score"])

    def test_online_score_handler_with_incomplete_arguments(self):
        """
        Test that API returns proper score if not-all args are passed.
        """
        request = {
            "account": "horns&hoofs", "login": "h&f",
            "method": "online_score", "token": TOKEN,
            "arguments": {
                "phone": "79175002040", "email": "stupnikov@otus.ru",
                "first_name": "John",
                "birthday": "01.01.1990", "gender": 1
            }
        }
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code)
        self.assertEqual(4.5, response["score"])

    def test_clients_interests_handler(self):
        """
        Test that clients interests API works as expected
        if correct request is sent.
        """
        kv = {"i:1": '["tv", "sport"]', "i:2": '["photo", "food"]'}
        self.fill_storage(kv)
        request = {
            "account": "horns&hoofs", "login": "h&f",
            "method": "clients_interests", "token": TOKEN,
            "arguments": {
                "client_ids": [1, 2]
            }
        }
        response, code = self.get_response(request)
        self.assertEqual(api.OK, code)
        self.assertEqual([u'tv', u'sport'], response[1])
        self.assertEqual([u'photo', u'food'], response[2])


# -----------------------------------------------------------------------------
# Main.

if __name__ == "__main__":
    unittest.main()
