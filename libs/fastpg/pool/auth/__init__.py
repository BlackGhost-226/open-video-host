from messages.readers import read_simple_packet
from messages.simple.backend.auth import AuthenticationOk, AuthenticationSASLContinue, AuthenticationSASLFinal
from messages.simple.frontend.auth import PasswordMessage, SASLInitialResponse, SASLResponse

from ..errors import InterfaceError
from .utils import saslprep, xor, wait

from asyncio import StreamReader, StreamWriter

import base64
import hashlib
import hmac
import secrets


async def clear_text(reader: StreamReader, writer: StreamWriter, passwd: str, init_pkt: bytes):
    writer.write(PasswordMessage.build({"password": [passwd]}))
    await writer.drain()
    while True:
        pkt = await read_simple_packet(reader)
        if AuthenticationOk.matches(pkt):
            break
    await wait(reader, "clear text authentication")
    return True

async def sasl(reader: StreamReader, writer: StreamWriter, passwd: str, init_pkt: bytes):
    # https://www.postgresql.org/docs/current/sasl-authentication.html
    # https://datatracker.ietf.org/doc/html/rfc7677
    # https://datatracker.ietf.org/doc/html/rfc5802

    prep_password = saslprep(passwd).encode("utf-8")
    c_nonce = secrets.token_urlsafe(16)

    client_first_bare = f"n=user,r={c_nonce}"
    
    writer.write(SASLInitialResponse.build({"mechanism": ["SCRAM-SHA-256"], "payload": [f"n,,{client_first_bare}".encode("ascii")]}))
    await writer.drain()

    server_signature = None

    while True:
        pkt = await read_simple_packet(reader)
        if AuthenticationOk.matches(pkt):
            break

        elif AuthenticationSASLContinue.matches(pkt):
            server_first_bytes = AuthenticationSASLContinue.parse(pkt)["sasl_data"][0]
            server_first_str = server_first_bytes.decode("ascii")
            params = dict(item.split("=", 1) for item in server_first_str.split(","))

            s_nonce = params["r"]
            salt = base64.b64decode(params["s"])
            iterations = int(params["i"])

            if not s_nonce.startswith(c_nonce):
                raise InterfaceError("Server SCRAM nonce does not match client nonce prefix")

            channel_binding = "c=biws"  # base64("n,,")
            nonce_param = f"r={s_nonce}"
            client_final_without_proof = f"{channel_binding},{nonce_param}"

            salted_password = hashlib.pbkdf2_hmac('sha256', prep_password, salt, iterations)
            client_key = hmac.new(salted_password, b"Client Key", hashlib.sha256).digest()
            stored_key = hashlib.sha256(client_key).digest()

            auth_message = f"{client_first_bare},{server_first_str},{client_final_without_proof}".encode("ascii")

            client_signature = hmac.new(stored_key, auth_message, hashlib.sha256).digest()
            client_proof = xor(client_key, client_signature)

            server_key = hmac.new(salted_password, b"Server Key", hashlib.sha256).digest()
            server_signature = hmac.new(server_key, auth_message, hashlib.sha256).digest()

            proof_b64 = base64.b64encode(client_proof).decode("ascii")
            client_final = f"{client_final_without_proof},p={proof_b64}"

            writer.write(SASLResponse.build({"data": [client_final.encode("ascii")]}))
            await writer.drain()

        elif AuthenticationSASLFinal.matches(pkt):
            server_final_bytes = AuthenticationSASLFinal.parse(pkt)["sasl_outcome"][0]
            params = dict(item.split("=", 1) for item in server_final_bytes.decode("ascii").split(","))
            
            received_sig = base64.b64decode(params["v"])
            if not hmac.compare_digest(received_sig, server_signature):
                raise InterfaceError("SCRAM server signature verification failed")
            
    await wait(reader, "sasl authentication")
    return True
