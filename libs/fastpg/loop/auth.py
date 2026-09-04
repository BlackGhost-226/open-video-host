from messages.simple.backend.auth import AuthenticationOk, AuthenticationCleartextPassword
from messages.simple.backend import ReadyForQuery
from messages.simple.frontend.auth import PasswordMessage
from messages.readers import read_simple_packet

from asyncio import StreamReader
from asyncio import StreamWriter

from typing import Callable


async def handle_authentication(client_reader: StreamReader, client_writer: StreamWriter, token_callback: Callable[[str], dict[str, str]]):
    # Curently unsupported by most python adapters:
    # https://www.postgresql.org/docs/current/sasl-authentication.html#SASL-OAUTHBEARER
    # https://datatracker.ietf.org/doc/html/rfc7628

    # So:
    client_writer.write(AuthenticationCleartextPassword.build({}))
    client_writer.drain()
    token = PasswordMessage.parse(await read_simple_packet(client_reader))["password"][0]

    client_writer.write(AuthenticationOk.build({}))
    client_writer.write(ReadyForQuery.build({"transaction_status": "I"}))
    await client_writer.drain()

    return token_callback(token)
