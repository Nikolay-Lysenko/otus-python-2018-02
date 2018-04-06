"""
A simple web server in plain Python.

Author: Nikolay Lysenko
"""


import socket
import threading
import multiprocessing
import logging
import argparse
import os


class FilesHTTPHandler(object):
    """
    Simple HTTPHandler that provides access to static files.

    :param root:
        root of a directory with static files that can be
        returned
    """

    def __init__(self, root):
        # type: (str) -> ...
        self.root = root
        self.http_request_end = '\r\n\r\n'
        self.chunk_size_in_bytes = 4096
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
        request = handler.receive_request()
        print 'Received {}'.format(request)
        client_socket.send('Answer')
        client_socket.close()

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
