#!/usr/bin/env python
# -*- coding: utf-8 -*-


"""
This script starts a web service which can process POST requests
of a particular structure (see homework description for details).
To study all possible options of configuring a service, execute this
from a terminal: `python api.py -h`.
To launch a service with default settings, execute:
`python api.py`.
After server is started, you can send requests to it. A sample commands
that can be executed from a terminal are provided at the `README.md`
file of the current directory.
"""


import os
import argparse
import json
import datetime
import logging
import hashlib
import uuid
from abc import ABCMeta, abstractmethod
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler
from weakref import WeakKeyDictionary

from scoring import get_score, get_interests


SALT = "Otus"
ADMIN_LOGIN = "admin"
ADMIN_SALT = "42"
OK = 200
BAD_REQUEST = 400
FORBIDDEN = 403
NOT_FOUND = 404
INVALID_REQUEST = 422
INTERNAL_ERROR = 500
ERRORS = {
    BAD_REQUEST: "Bad Request",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    INVALID_REQUEST: "Invalid Request",
    INTERNAL_ERROR: "Internal Server Error",
}
UNKNOWN = 0
MALE = 1
FEMALE = 2
GENDERS = {
    UNKNOWN: "unknown",
    MALE: "male",
    FEMALE: "female",
}


# -----------------------------------------------------------------------------
# Descriptors for fields validation.

class BaseField(object):
    """
    Abstract descriptor representing a field of POST request.

    :param required:
        if it is `True`, field value must be passed explicitly
    :param nullable:
        if it is `True`, filed value can be empty, default is `False`
    """
    __metaclass__ = ABCMeta

    def __init__(self, required, nullable=False):
        self.data = WeakKeyDictionary()
        self.required = required
        self.nullable = nullable

    def __get__(self, instance, owner):
        value = self.data.get(instance)
        return value

    @abstractmethod
    def __set__(self, instance, value):
        # Check that a value is in accordance with instance settings.
        if value is None and self.required:
            raise ValueError("Required fields must be passed explicitly.")
        if not value and not self.nullable:
            raise ValueError("Empty value in a non-nullable field: %s" % value)


class CharField(BaseField):
    """A descriptor that prohibits non-char values."""

    def __set__(self, instance, value):
        super(CharField, self).__set__(instance, value)
        if value and not isinstance(value, (str, unicode)):
            raise ValueError("Non-char values are not allowed: %s" % value)
        self.data[instance] = value


class ArgumentsField(BaseField):
    """A descriptor that validates nested requests."""

    def __set__(self, instance, value):
        super(ArgumentsField, self).__set__(instance, value)
        if value and not isinstance(value, dict):
            raise ValueError("Non-dict values are not allowed: %s" % value)
        self.data[instance] = value


class EmailField(CharField):
    """A descriptor that validates email address."""

    def __set__(self, instance, value):
        super(EmailField, self).__set__(instance, value)
        if value:
            split_value = value.split('@')
            email_is_invalid = (
                len(split_value) != 2
                or len(split_value[0]) == 0
                or len(split_value[1]) == 0
                or '.' not in split_value[1]
            )
            if email_is_invalid:
                raise ValueError("It does not look like an email: %s" % value)
        self.data[instance] = value


class PhoneField(BaseField):
    """A descriptor that validates phone number."""

    def __set__(self, instance, value):
        super(PhoneField, self).__set__(instance, value)
        if value:
            if not isinstance(value, (str, unicode, int)):
                raise ValueError("Value is neither char nor int: %s" % value)
            try:
                value = int(value)
            except TypeError:
                raise ValueError("Non-digits are in phone value: %s" % value)
            value = str(value)
            phone_validity = (
                len(value) == 11
                and value.startswith('7')
            )
            if not phone_validity:
                raise ValueError("It does not look like a phone: %s" % value)
        self.data[instance] = value


class DateField(CharField):
    """
    A descriptor that prohibits non-date values
    and forces 'DD.MM.YYYY' format.
    """

    def __set__(self, instance, value):
        super(DateField, self).__set__(instance, value)
        if value:
            try:
                datetime.datetime.strptime(value, '%d.%m.%Y')
            except ValueError:
                raise ValueError("Date %s not in format 'DD.MM.YYYY'" % value)
        self.data[instance] = value


class BirthDayField(DateField):
    """A descriptor that validates birthdays."""

    def __set__(self, instance, value):
        super(BirthDayField, self).__set__(instance, value)
        if value:
            today = datetime.date.today()
            value_as_date = (
                datetime.datetime.strptime(value, '%d.%m.%Y').date()
                if value
                else None
            )
            days_per_year = 365.25
            max_age = 70
            if (today - value_as_date).days / days_per_year > max_age:
                raise ValueError('Sorry, too distant birthday: %s' % value)
        self.data[instance] = value


class GenderField(BaseField):
    """A descriptor that validates gender codes."""

    def __set__(self, instance, value):
        super(GenderField, self).__set__(instance, value)
        if value and value not in GENDERS.keys():
            raise ValueError("Invalid gender code: %s" % value)
        self.data[instance] = value


class ClientIDsField(BaseField):
    """A descriptor that validates sequences of client IDs."""

    def __set__(self, instance, value):
        super(ClientIDsField, self).__set__(instance, value)
        if value:
            if not isinstance(value, list):
                raise ValueError("IDs must be stored in array: %s" % value)
            value_types = set([type(x) for x in value])
            if value_types != {int}:
                bad_types = [x for x in value_types if x != int]
                raise ValueError("Non-integer types in IDs: %s" % bad_types)
        self.data[instance] = value


# -----------------------------------------------------------------------------
# Classes for requests validation.

class ClientsInterestsRequest(object):
    """
    A class representing nested request to interests API.
    """
    client_ids = ClientIDsField(required=True)
    date = DateField(required=False, nullable=True)

    def __init__(self, client_ids=None, date=None):
        self.client_ids = client_ids
        self.date = date


class OnlineScoreRequest(object):
    """
    A class representing nested request to scoring API.
    """
    first_name = CharField(required=False, nullable=True)
    last_name = CharField(required=False, nullable=True)
    email = EmailField(required=False, nullable=True)
    phone = PhoneField(required=False, nullable=True)
    birthday = BirthDayField(required=False, nullable=True)
    gender = GenderField(required=False, nullable=True)

    def __init__(
            self,
            first_name=None, last_name=None, email=None, phone=None,
            birthday=None, gender=None
            ):
        pairwise_validity = (
            (first_name and last_name)
            or (email and phone)
            or (birthday and gender)
        )
        if not pairwise_validity:
            raise ValueError("No pairs where both values are non-empty.")
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.phone = phone
        self.birthday = birthday
        self.gender = gender


class MethodRequest(object):
    """
    A class representing top-level POST request to any of the two APIs.
    """
    account = CharField(required=False, nullable=True)
    login = CharField(required=True, nullable=True)
    token = CharField(required=True, nullable=True)
    arguments = ArgumentsField(required=True, nullable=True)
    method = CharField(required=True, nullable=False)

    @property
    def is_admin(self):
        return self.login == ADMIN_LOGIN

    def __init__(
            self,
            account=None, login=None, token=None, arguments=None, method=None
            ):
        self.account = account
        self.login = login
        self.token = token
        self.arguments = arguments
        self.method = method


# -----------------------------------------------------------------------------
# Functions with business logic.

def check_auth(request):
    # type: (MethodRequest) -> type(None)
    """Authenticate request by token."""
    if request.is_admin:
        digest = hashlib.sha512(
            datetime.datetime.now().strftime("%Y%m%d%H") + ADMIN_SALT
        ).hexdigest()
    else:
        digest = hashlib.sha512(
            request.account + request.login + SALT
        ).hexdigest()
    if digest == request.token:
        return True
    return False


def clients_interests_handler(request, context, store):
    # type: (MethodRequest, dict, bool) -> (str, int)
    """Handle request for clients interests."""
    response, code = {}, OK
    try:
        nested_request = ClientsInterestsRequest(**request.arguments)
    except TypeError as e:
        logging.exception('Extra arguments in request: ')
        response, code = str(e), INVALID_REQUEST
        return response, code
    except ValueError as e:
        logging.exception('Validation error: ')
        response, code = str(e), BAD_REQUEST
        return response, code
    context['nclients'] = len(nested_request.client_ids)
    for client_id in nested_request.client_ids:
        response[client_id] = get_interests(store, client_id)
    return response, code


def online_score_handler(request, context, store):
    # type: (MethodRequest, dict, bool) -> (str, int)
    """Handle request for scores."""
    response, code = {}, OK
    try:
        nested_request = OnlineScoreRequest(**request.arguments)
    except TypeError as e:
        logging.exception('Extra arguments in request: ')
        response, code = str(e), INVALID_REQUEST
        return response, code
    except ValueError as e:
        logging.exception('Validation error: ')
        response, code = str(e), BAD_REQUEST
        return response, code
    fields = [
        'first_name', 'last_name', 'email', 'phone', 'birthday', 'gender'
    ]
    context['has'] = [
        field for field in fields if nested_request.__getattribute__(field)
    ]
    score = 42 if request.is_admin else get_score(store, **request.arguments)
    response = {'score': score}
    return response, code


def method_handler(request, context, store):
    # type: (dict, dict, bool) -> (str, int)
    """Redirect arbitrary request to corresponding handler."""
    try:
        request = MethodRequest(**request['body'])
    except (KeyError, TypeError, ValueError) as e:
        logging.exception('Can not validate POST request: ')
        response, code = str(e), INVALID_REQUEST
        return response, code
    if not check_auth(request):
        response, code = ERRORS[FORBIDDEN], FORBIDDEN
        return response, code
    handlers = {
        'clients_interests': clients_interests_handler,
        'online_score': online_score_handler
    }
    try:
        response, code = handlers[request.method](request, context, store)
    except KeyError:
        logging.exception('Unrecognized method: ')
        response = 'Unrecognized method: %s' % request.method
        code = INVALID_REQUEST
    return response, code


# -----------------------------------------------------------------------------
# Web server.

class MainHTTPHandler(BaseHTTPRequestHandler):
    router = {
        "method": method_handler
    }
    store = None

    @staticmethod
    def get_request_id(headers):
        return headers.get('HTTP_X_REQUEST_ID', uuid.uuid4().hex)

    def do_POST(self):
        response, code = {}, OK
        context = {"request_id": self.get_request_id(self.headers)}
        request = None
        try:
            data_string = self.rfile.read(int(self.headers['Content-Length']))
            request = json.loads(data_string)
        except:
            logging.exception('Can not parse JSON: ')
            code = BAD_REQUEST

        if request:
            path = self.path.strip("/")
            msg = "%s: %s %s" % (self.path, data_string, context["request_id"])
            logging.info(msg)
            if path in self.router:
                try:
                    response, code = self.router[path](
                        {"body": request, "headers": self.headers},
                        context, self.store
                    )
                except Exception, e:
                    logging.exception("Unexpected error: %s" % e)
                    code = INTERNAL_ERROR
            else:
                code = NOT_FOUND

        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        if code not in ERRORS:
            r = {
                "response": response,
                "code": code
            }
        else:
            r = {
                "error": response or ERRORS.get(code, "Unknown Error"),
                "code": code
            }
        context.update(r)
        logging.info(context)
        self.wfile.write(json.dumps(r))
        return


# -----------------------------------------------------------------------------
# User interaction tools.

def parse_cli_args():
    # type: () -> argparse.Namespace
    """
    Parse arguments passed via Command Line Interface (CLI).

    :return:
        namespace with arguments
    """
    parser = argparse.ArgumentParser(description='Requests to API')
    parser.add_argument(
        '-p', '--port', type=int, default=8080,
        help='port that is listened by the server'
    )
    parser.add_argument(
        '-l', '--logging_file', type=str, default=None,
        help='full path to file where logs of script execution will be stored,'
             'by default stdout is used instead of a file'
    )
    cli_args = parser.parse_args()
    return cli_args


def set_logging(logging_filename):
    # type: (Optional[str]) -> type(None)
    """
    Set logging according to homework specification.

    :param logging_filename:
        name of file where logs are written
        or `None` if stdout should be used
    :return:
        None
    """
    fname_passed = logging_filename is not None
    if fname_passed and not os.path.isdir(os.path.dirname(logging_filename)):
        os.makedirs(logging_filename)
    msg_format = '[%(asctime)s] %(levelname).1s %(message)s'
    datetime_fmt = '%Y.%m.%d %H:%M:%S'
    logging.basicConfig(
        filename=logging_filename,
        format=msg_format,
        datefmt=datetime_fmt,
        level=logging.INFO
    )
    logging.info("Logging is set.")


def main():
    cli_args = parse_cli_args()
    set_logging(cli_args.logging_file)
    server = HTTPServer(("localhost", cli_args.port), MainHTTPHandler)
    logging.info("Starting server at %s" % cli_args.port)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    except:
        logging.exception('Unhandled exception: ')
    server.server_close()


if __name__ == "__main__":
    main()
