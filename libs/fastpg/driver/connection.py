# TODO https://docs.python.org/3/library/contextlib.html

import socket
from urllib.parse import urlsplit
from typing import Callable

from .cursor import Cursor
from .type_objects import array_map, populate_array_map
from .errors import Warning, InterfaceError
from . import wait
from .auth import clear_text, sasl

from messages.simple.frontend import Query
from messages.simple.backend.auth import AuthenticationCleartextPassword, AuthenticationSASL
from messages.special import StartupMessage
from messages.readers import sync_read_simple_packet
from messages import MessageBase


def open_connection(host: str, port: int, timeout: float = None):
    sock = socket.create_connection((host, port), timeout=timeout)
    sock.setblocking(True)
    reader = sock.makefile('rb', buffering=0)
    writer = sock.makefile('wb', buffering=0)
    return reader, writer, sock

def close_connection(reader, writer, sock):
    if writer and not getattr(writer, "closed", True):
        try:
            writer.flush()
        except (ValueError, OSError):
            pass

    for stream in (reader, writer):
        if stream and not getattr(stream, "closed", True):
            try:
                stream.close()
            except (ValueError, OSError):
                pass

    if sock:
        try:
            sock.shutdown(socket.SHUT_RDWR)
        except (ValueError, OSError):
            pass
        finally:
            try:
                sock.close()
            except (ValueError, OSError):
                pass


class Connection:
    def __init__(self, db_uri: str, timeout: float = None):
        self.auth_options: list[tuple[MessageBase, Callable]] = [(AuthenticationCleartextPassword, clear_text), (AuthenticationSASL, sasl)]
        self.transaction_began = False

        uri_data = urlsplit(db_uri)
        if uri_data.scheme != "postgresql":
            raise Warning("The protocol in the URI provided is not 'postgresql'.")

        host, port = uri_data.netloc.split("@")[1].split(":")
        self.reader, self.writer, self.sock = open_connection(host, port, timeout)

        user, passwd = uri_data.netloc.split("@")[0].split(":")
        self._startup(user, passwd, uri_data.path[1:])

        if array_map == {}:
            populate_array_map(self)

    def _startup(self, user: str, passwd: str, db: str):
        start_pkt = StartupMessage.build({'parameters': [{"user": [user], "database": [db], "application_name": ["fastpg_driver"], "client_encoding": ["UTF8"]}]})
        self.writer.write(start_pkt)
        self.writer.flush()

        pkt = sync_read_simple_packet(self.reader)
        succeeded = False
        for option in self.auth_options:
            if option[0].matches(pkt):
                succeeded = option[1](self.reader, self.writer, passwd, pkt)
                break
        if not succeeded:
            raise InterfaceError("Cannot authenticate into the database because the database's authentication method is not supported.")
        

    def close(self):
        if self.transaction_began:
            self.rollback()
        close_connection(self.reader, self.writer, self.sock)

    def __del__(self):
        self.close()

    def commit(self):
        self.writer.write(Query.build({"query": ["COMMIT;"]}))
        self.writer.flush()
        wait(self.reader, "commiting")
        self.transaction_began = False

    def rollback(self):
        self.writer.write(Query.build({"query": ["ROLLBACK;"]}))
        self.writer.flush()
        wait(self.reader, "rollbacking")
        self.transaction_began = False

    def cursor(self):
        return Cursor(self)
