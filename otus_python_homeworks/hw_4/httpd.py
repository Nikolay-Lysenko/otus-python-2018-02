"""
A simple web server in plain Python.

Author: Nikolay Lysenko
"""


import argparse
import logging
import os
import threading
import multiprocessing
import socket
import urlparse
import urllib
import mimetypes
import datetime
from collections import OrderedDict


OK = 200
FORBIDDEN = 403
NOT_FOUND = 404
METHOD_NOT_ALLOWED = 405

MESSAGES = {
    OK: "OK",
    FORBIDDEN: "Forbidden",
    NOT_FOUND: "Not Found",
    METHOD_NOT_ALLOWED: "Method Not Allowed"
}


class HTTPResponseMaker(object):
    """
    This class provides interface for making HTTP responses.

    :param status:
        status of HTTP response
    :param method:
        requested method (such as GET or HEAD)
    :param path:
        requested path to a static file
    """
    status_line_template = "HTTP/1.1 {} {}"
    http_header_end = '\r\n\r\n'

    def __init__(self, status, method, path):
        # type: (int, str, str) -> ...
        self.status = status
        self.method = method
        self.path = path
        self.headers = None
        self.body = None

    def __prepare_response(self):
        # type: (...) -> type(None)
        # Fill headers and body.
        self.headers = OrderedDict({
            "Date": None,
            "Server": "Otus-Python-HW04",
            "Content-Length": self.__measure_content_length(),
            "Content-Type": self.__infer_content_type(),
            "Connection": self.__decide_about_connection()
        })
        self.body = self.__make_body() if self.method == 'GET' else ''

    def __measure_content_length(self):
        # type: (...) -> int
        # Figure out content length.
        result = (
            os.path.getsize(self.path)
            if self.path is not None and self.status == OK
            else 0
        )
        return result

    def __infer_content_type(self):
        # type: (...) -> str
        # Return type of content in a proper format.
        content_type, content_encoding = (
            mimetypes.guess_type(self.path)
            if self.path is not None
            else ('text/html', 'utf-8')
        )
        return content_type

    def __decide_about_connection(self):
        # type: (...) -> str
        # Decide whether a client should be told to close connection.
        return 'keep-alive' if self.method == 'HEAD' else 'close'

    def __make_body(self):
        # type: (...) -> str
        # Make body of a response.
        if self.path is None or self.method != 'GET':
            return ''
        with open(self.path, 'r') as source_file:
            body = source_file.read()
        return body

    @staticmethod
    def __get_current_time():
        # type: (...) -> str
        # Return a string representation of a date in accordance with HTTP/1.1
        res = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        return res

    def render_response(self):
        # type: (...) -> str
        """
        Return response based on class attributes.
        """
        status_line = self.status_line_template.format(
            self.status, MESSAGES[self.status]
        )
        self.__prepare_response()
        self.headers['Date'] = self.__get_current_time()
        headers = '\r\n'.join(
            ['{}: {}'.format(k, v) for k, v in self.headers.items()]
        )
        response = (
            status_line + '\r\n' + headers + self.http_header_end + self.body
        )
        logging.debug('Response is: ')
        logging.debug(status_line)
        logging.debug(headers)
        return response


class FilesHTTPHandler(object):
    """
    Simple HTTP handler that provides access to static files.

    :param root:
        root of a directory with static files that can be
        returned
    """
    http_request_end = '\r\n\r\n'
    chunk_size_in_bytes = 4096
    allowed_methods = ['GET', 'HEAD']

    def __init__(self, root):
        # type: (str) -> ...
        self.root = root
        self.client_socket = None

    def set_client_socket(self, client_socket):
        # type: (socket.socket) -> type(None)
        """Set client socket."""
        self.client_socket = client_socket

    def receive_request(self):
        # type: (...) -> str
        """
        Receive full request sent by client.
        The method relies on assumption that every valid request
        ends with `self.http_request_end`.
        """
        request = ''
        while True:
            chunk = self.client_socket.recv(self.chunk_size_in_bytes)
            request += chunk
            if self.http_request_end in request:
                break
            if not chunk:
                logging.info("Request ended with empty chunk.")
                break
        request = request.split(self.http_request_end)[0]
        return request

    def __extract_method(self, request):
        # type (str) -> str
        # Extract requested method from raw request.
        try:
            method = request.split(' ')[0]
        except:
            raise ValueError('Bad request')
        if method not in self.allowed_methods:
            raise ValueError(MESSAGES[METHOD_NOT_ALLOWED])
        return method

    @staticmethod
    def __extract_filepath(request):
        # type (str) -> str
        # Extract path to requested file from raw request.
        try:
            url = request.split(' ')[1]
            parsed_url = urlparse.urlparse(url)
            path = urllib.unquote(parsed_url.path).decode('utf8').lstrip('/')
            path = os.path.join(os.path.dirname(__file__), path)
        except:
            raise ValueError('Bad request')
        if os.path.isdir(path):
            path += '/'
        return path

    def parse_request(self, request):
        # type: (str) -> (int, str, str)
        """
        Parse raw request.
        If path is a directory, point to `index.html` file from there.
        If resulting path does not exist or looks suspiciously,
        replace path with `None`.
        """
        try:
            method = self.__extract_method(request)
            path = self.__extract_filepath(request)
        except ValueError as e:
            msg = str(e)
            if 'Bad request' in msg or MESSAGES[METHOD_NOT_ALLOWED] in msg:
                return METHOD_NOT_ALLOWED, '', ''
            else:
                raise e
        if path.endswith('/'):
            path = os.path.join(path, 'index.html')
            if not os.path.isfile(path):
                return FORBIDDEN, method, None
        if not os.path.isfile(path) or '../' in path:
            return NOT_FOUND, method, None
        return OK, method, path

    def handle(self):
        # type: (...) -> type(None)
        """
        Do all work that relates to a client socket.
        """
        request = self.receive_request()
        logging.debug('Received {}'.format(request))
        status, method, path = self.parse_request(request)
        logging.debug(
            'Status, method, path: {}, {}, {}'.format(status, method, path)
        )
        response_maker = HTTPResponseMaker(status, method, path)
        response = response_maker.render_response()
        self.client_socket.sendall(response)
        self.client_socket.close()


class VanillaHTTPServer(object):
    """
    A simple server built with threading architecture.

    :param host:
        host on which server should operate
    :param port:
        port which should be listened by the server
    :param max_backlog:
        maximum number of queued client connections
    """

    def __init__(self, host, port, root, handler, max_backlog=5):
        # type: (str, int, str, str, int) -> ...
        self.host = host
        self.port = port
        self.root = root
        self.str_to_type = {'files_handler': FilesHTTPHandler}
        self.handler = None
        self.__set_http_handler(handler)
        self.max_backlog = max_backlog
        self.socket = None
        self.__make_socket()

    def __set_http_handler(self, handler_name):
        # type: (str) -> type(None)
        # Validate type of HTTP requests handler and store it as attribute.
        if handler_name not in self.str_to_type.keys():
            raise ValueError("Unknown handler type: {}".format(handler_name))
        self.handler = handler_name

    def __make_socket(self):
        # type: (...) -> ...
        # Make server-side socket.
        try:
            # 'AF' in `socket.AF_INET` stands for 'address family',
            # 'AF_INET' means that socked can be bound to a host and a port.
            # 'SOCK' in `socket.SOCK_STREAM` stands for socket type.
            # 'SOCK_STREAM' is the most applicable type.
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # Binding can fail without below command.
            # `SOL_SOCKET` is a level, and `SO_REUSEADDR` variable is set
            # to`True` at this level.
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(self.max_backlog)
            logging.info('Socket listens {}:{}'.format(self.host, self.port))
        except Exception as e:
            logging.exception('Can not make socket: ')
            raise e

    def __handle_client_connection(self, client_socket):
        # type: (socket.socket) -> type(None)
        handler = self.str_to_type[self.handler](self.root)
        handler.set_client_socket(client_socket)
        handler.handle()

    def serve_forever(self):
        # type: (...) -> type(None)
        """
        Launch a server.
        """
        while True:
            client_socket = None
            try:
                client_socket, client_addr = self.socket.accept()
                client_from = '{}:{}'.format(client_addr[0], client_addr[1])
                logging.info('Accepted connection from {}'.format(client_from))
                client_handler = threading.Thread(
                    target=self.__handle_client_connection,
                    args=(client_socket,)
                )
                client_handler.start()
            except KeyboardInterrupt:
                raise KeyboardInterrupt
            except:
                if client_socket is not None:
                    client_socket.close()
                logging.exception('Can not handle a request: ')

    def shut_down(self):
        # type: (...) -> type(None)
        """
        Shut down server.
        """
        self.socket.close()


def parse_cli_args():
    # type: () -> argparse.Namespace
    """
    Parse arguments passed via Command Line Interface (CLI).

    :return:
        namespace with arguments
    """
    parser = argparse.ArgumentParser(description='Web server in plain Python')
    parser.add_argument(
        '-hs', '--host', type=str, default="127.0.0.1",
        help='host of the server, default is localhost'
    )
    parser.add_argument(
        '-p', '--port', type=int, default=8080,
        help='port that is listened by the server, default is 8080'
    )
    parser.add_argument(
        '-w', '--workers', type=int, default=4,
        help='number of separate processes for running the server'
    )
    parser.add_argument(
        '-r', '--root', type=str, default='httptest',
        help='root of a directory with static files shared by the server'
    )
    parser.add_argument(
        '-l', '--logging_file', type=str, default=None,
        help='full path to file where server logs will be stored,'
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
    if logging_filename is not None:
        logging_dir = os.path.dirname(logging_filename)
        if not os.path.isdir(logging_dir):
            os.makedirs(logging_dir)
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
    server = VanillaHTTPServer(
        cli_args.host, cli_args.port, cli_args.root, handler='files_handler'
    )
    # `multiprocessing.Pool` is not used below, because `KeyboardInterrupt`
    # never reaches a parent process if it is used.
    workers = []
    try:
        for i in range(cli_args.workers):
            worker = multiprocessing.Process(target=server.serve_forever)
            workers.append(worker)
            worker.start()
        for worker in workers:
            worker.join()
    except KeyboardInterrupt:
        for worker in workers:
            if worker:
                worker.terminate()
    except:
        logging.exception('Unhandled exception: ')
    server.shut_down()


if __name__ == '__main__':
    main()
