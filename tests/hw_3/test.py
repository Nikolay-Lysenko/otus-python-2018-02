import unittest

from otus_python_homeworks.hw_3 import api, store


TOKEN = (
    "55cc9ce545bcd144300fe9efc28e65d415b923ebb6be1e19d2750a2c03e80dd209a27954"
    "dca045e5bb12418e7d89b6d718a9e35af34e14e1d5bcd5a08f21fc95"
)


# -----------------------------------------------------------------------------
# Decorators.

def cases(test_inputs):
    """
    A decorator for passing various test cases.
    """

    def nested_decorator(func):
        def wrapper(*args, **kwargs):
            for test_input in test_inputs:
                test_input = (
                    (test_input,)
                    if not isinstance(test_input, tuple)
                    else test_input
                )
                arguments = args + test_input
                func(*arguments, **kwargs)
        return wrapper

    return nested_decorator


# -----------------------------------------------------------------------------
# Mocks.

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


class DescriptorMock(object):
    """
    Mock for a class that has fields with descriptors.
    """
    def __init__(self, value):
        self.value = value


# -----------------------------------------------------------------------------
# Unit tests.

class TestDescriptors(unittest.TestCase):
    """
    Test all customized fields.
    """
    
    def setUp(self):
        self.error_msg = ''

    def test_char_field_with_non_char(self):
        """Test `CharField` descriptor with integer value."""
        DescriptorMock.value = api.CharField(required=True)
        try:
            DescriptorMock(1)
        except ValueError as e:
            self.error_msg = str(e)
        self.assertTrue('Non-char' in self.error_msg)

    def test_char_field_with_empty_string(self):
        """Test `CharField` descriptor with empty string."""
        DescriptorMock.value = api.CharField(required=True)
        try:
            DescriptorMock('')
        except ValueError as e:
            self.error_msg = str(e)
        self.assertTrue('Empty' in self.error_msg)

    def test_char_field_with_valid_value(self):
        """Test `CharField` descriptor with valid chars."""
        DescriptorMock.value = api.CharField(required=True)
        try:
            DescriptorMock("a")
            DescriptorMock("A + b")
        except Exception as e:
            self.error_msg = str(e)
        self.assertFalse(self.error_msg)

    def test_arguments_field_with_non_char(self):
        """Test `ArgumentsField` descriptor with integer value."""
        DescriptorMock.value = api.ArgumentsField(required=True)
        try:
            DescriptorMock(1)
        except ValueError as e:
            self.error_msg = str(e)
        self.assertTrue('Non-dict' in self.error_msg)

    def test_arguments_field_with_empty_dict(self):
        """Test `ArgumentsField` descriptor with empty dict."""
        DescriptorMock.value = api.ArgumentsField(required=True)
        try:
            DescriptorMock({})
        except ValueError as e:
            self.error_msg = str(e)
        self.assertTrue('Empty' in self.error_msg)

    def test_arguments_field_with_valid_value(self):
        """Test `ArgumentsField` descriptor with valid dicts."""
        DescriptorMock.value = api.ArgumentsField(required=True)
        try:
            DescriptorMock({"a": 1})
            DescriptorMock({1: 2, 3: 5})
        except Exception as e:
            self.error_msg = str(e)
        self.assertFalse(self.error_msg)
        
    def test_email_field_without_at(self):
        """Test `EmailField` descriptor without @ symbol."""
        DescriptorMock.value = api.EmailField(required=True)
        try:
            DescriptorMock("me-at-otus.ru")
        except ValueError as e:
            self.error_msg = str(e)
        self.assertTrue('look like' in self.error_msg)

    def test_email_field_without_dot(self):
        """Test `EmailField` descriptor without dot."""
        DescriptorMock.value = api.EmailField(required=True)
        try:
            DescriptorMock("me@otusru")
        except ValueError as e:
            self.error_msg = str(e)
        self.assertTrue('look like' in self.error_msg)

    def test_email_field_with_valid_value(self):
        """Test `EmailField` descriptor with valid email."""
        DescriptorMock.value = api.EmailField(required=True)
        try:
            DescriptorMock("me@otus.ru")
            DescriptorMock("john-doe@example.com")
        except Exception as e:
            self.error_msg = str(e)
        self.assertFalse(self.error_msg)

    def test_phone_field_with_non_char(self):
        """Test `PhoneField` descriptor with list value."""
        DescriptorMock.value = api.PhoneField(required=True)
        try:
            DescriptorMock([8, 8, 0, 0, 2, 0, 0, 0])
        except ValueError as e:
            self.error_msg = str(e)
        self.assertTrue('neither char nor int' in self.error_msg)

    def test_phone_field_with_non_digits(self):
        """Test `PhoneField` descriptor with non-digits."""
        DescriptorMock.value = api.PhoneField(required=True)
        try:
            DescriptorMock("8903abc")
        except ValueError as e:
            self.error_msg = str(e)
        self.assertTrue('Non-digits' in self.error_msg)

    def test_phone_field_starting_with_non_seven(self):
        """Test `PhoneField` descriptor with wrong first digit."""
        DescriptorMock.value = api.PhoneField(required=True)
        try:
            DescriptorMock("89030000000")
        except ValueError as e:
            self.error_msg = str(e)
        self.assertTrue('look like' in self.error_msg)

    def test_phone_field_starting_with_wrong_lenght(self):
        """Test `PhoneField` descriptor with wrong first digit."""
        DescriptorMock.value = api.PhoneField(required=True)
        try:
            DescriptorMock("7903000000")
        except ValueError as e:
            self.error_msg = str(e)
        self.assertTrue('look like' in self.error_msg)

    def test_phone_field_with_valid_value(self):
        """Test `PhoneField` descriptor with valid dicts."""
        DescriptorMock.value = api.PhoneField(required=True)
        try:
            DescriptorMock("79030000000")
            DescriptorMock(79030000000)
        except Exception as e:
            self.error_msg = str(e)
        self.assertFalse(self.error_msg)

    def test_date_field_with_wrong_format(self):
        """Test `DateField` descriptor with wrong format."""
        DescriptorMock.value = api.DateField(required=True)
        try:
            DescriptorMock("1990.01.01")
        except ValueError as e:
            self.error_msg = str(e)
        self.assertTrue('not in format' in self.error_msg)

    def test_date_field_with_valid_value(self):
        """Test `DateField` descriptor with valid dates."""
        DescriptorMock.value = api.DateField(required=True)
        try:
            DescriptorMock("01.01.1990")
            DescriptorMock("30.12.1890")
        except Exception as e:
            self.error_msg = str(e)
        self.assertFalse(self.error_msg)

    def test_birthday_field_with_too_old_date(self):
        """Test `BirthDayField` descriptor with too old date."""
        DescriptorMock.value = api.BirthDayField(required=True)
        try:
            DescriptorMock("01.01.1900")
        except ValueError as e:
            self.error_msg = str(e)
        self.assertTrue('too distant' in self.error_msg)

    def test_birthday_field_with_valid_value(self):
        """Test `BirthDayField` descriptor with valid dates."""
        DescriptorMock.value = api.BirthDayField(required=True)
        try:
            DescriptorMock("01.01.1990")
            DescriptorMock("30.12.1995")
        except Exception as e:
            self.error_msg = str(e)
        self.assertFalse(self.error_msg)

    def test_gender_field_with_wrong_code(self):
        """Test `GenderField` descriptor with broken code."""
        DescriptorMock.value = api.GenderField(required=True)
        try:
            DescriptorMock(3)
        except ValueError as e:
            self.error_msg = str(e)
        self.assertTrue('Invalid' in self.error_msg)

    def test_gender_field_with_valid_value(self):
        """Test `GenderField` descriptor with valid dates."""
        DescriptorMock.value = api.GenderField(required=True)
        try:
            DescriptorMock(1)
            DescriptorMock(2)
        except Exception as e:
            self.error_msg = str(e)
        self.assertFalse(self.error_msg)

    def test_client_ids_field_with_non_array(self):
        """Test `ClientIDsField` descriptor with non-array."""
        DescriptorMock.value = api.ClientIDsField(required=True)
        try:
            DescriptorMock({"a": 1})
        except ValueError as e:
            self.error_msg = str(e)
        self.assertTrue('array' in self.error_msg)

    def test_client_ids_field_with_non_int(self):
        """Test `ClientIDsField` descriptor with non-int element."""
        DescriptorMock.value = api.ClientIDsField(required=True)
        try:
            DescriptorMock([1, 2, "3"])
        except ValueError as e:
            self.error_msg = str(e)
        self.assertTrue('Non-integer' in self.error_msg)

    def test_client_ids_field_with_valid_value(self):
        """Test `ClientIDsField` descriptor with valid dates."""
        DescriptorMock.value = api.ClientIDsField(required=True)
        try:
            DescriptorMock([1, 2, 3])
            DescriptorMock([100])
        except Exception as e:
            self.error_msg = str(e)
        self.assertFalse(self.error_msg)


class TestInMemoryStorage(unittest.TestCase):
    """
    Tests of `InMemoryStorage` class.
    """

    def setUp(self):
        self.storage = store.InMemoryStorage()
        self.error_msg = ''

    def test_cache_set_and_cache_get(self):
        """Test `cache_get` and `cache_set` methods."""
        self.storage.cache_set("1", "a", 60)
        result = self.storage.cache_get("1")
        self.assertEqual("a", result)

    def test_get(self):
        """Test `get` method."""
        try:
            self.storage.get("2")
        except KeyError as e:
            self.error_msg = str(e)
        self.assertTrue('is absent' in self.error_msg)


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
