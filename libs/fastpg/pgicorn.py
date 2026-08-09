# The script is using the old messages syntax, do not run it or test it.
# If testing is needed go to tests.py file.

import asyncio
from asyncio import StreamReader
from asyncio import StreamWriter
import struct
from messages.special import StartupMessage, SSLRequest, GSSENCRequest, CancelRequest
from messages.simple.frontend import Query


async def read_special_packet(reader: StreamReader):
    len_bytes = await reader.readexactly(4)
    length = struct.unpack('!I', len_bytes)[0]
    rest = await reader.readexactly(length - 4)
    return len_bytes + rest

async def handle_cancel(id, key):
    pass

def build_postgres_error(message: str, code: str = "42501") -> bytes:
    fields = [
        b'S' + b'ERROR',
        b'C' + code.encode('utf-8'),
        b'M' + message.encode('utf-8'),
        b'\x00'
    ]
    payload = b'\x00'.join(fields)
    return b'E' + struct.pack('!I', 4 + len(payload)) + payload

class Server:
    def __init__(self, app_obj, host: str, port: int, db_host: str, db_port: int):
        self.app = app_obj
        self.host = host
        self.port = port
        self.db_host = db_host
        self.db_port = db_port

    def run(self):
        #uvloop.install()

        async def _main():
            server = await asyncio.start_server(
                lambda r, w: self._handle_connection(r, w), 
                self.host, 
                self.port
            )
            async with server:
                await server.serve_forever()

        try:
            asyncio.run(_main())
        except KeyboardInterrupt:
            pass

    async def _handle_connection(self, client_reader: StreamReader, client_writer: StreamWriter):
        startup_packet = None
        ssl_negotiated = False
        gssenc_negotiated = False
        while True:
            try:
                startup_packet = await read_special_packet(client_reader)
                if startup_packet == StartupMessage:
                    break

                elif startup_packet == SSLRequest:
                    if ssl_negotiated:
                        raise ConnectionError("Client sent duplicate SSLRequest")
                    client_writer.write(b'N')
                    await client_writer.drain()
                    ssl_negotiated = True

                elif startup_packet == GSSENCRequest:
                    if gssenc_negotiated:
                        raise ConnectionError("Client sent duplicate GSSENCRequest")
                    client_writer.write(b'N')
                    await client_writer.drain()
                    gssenc_negotiated = True

                elif startup_packet == CancelRequest:
                    cancel_req = CancelRequest(startup_packet)
                    await handle_cancel(cancel_req.process_ID, cancel_req.secret_key)
                    client_writer.close()
                    return
                
                else:
                    client_writer.close()
                    return
                
            except Exception:
                client_writer.close()
                return

        params = StartupMessage(startup_packet)

        try:
            backend_reader, backend_writer = await asyncio.open_connection(self.db_host, self.db_port)
            backend_writer.write(startup_packet)
            await backend_writer.drain()
        except Exception as e:
            client_writer.write(build_postgres_error("Database backend unreachable."))
            await client_writer.drain()
            client_writer.close()
            return

        # Forward Backend -> Client asynchronously
        async def forward_backend():
            try:
                while True:
                    data = await backend_reader.read(8192)
                    if not data: break
                    client_writer.write(data)
                    await client_writer.drain()
            except Exception: pass

        backend_task = asyncio.create_task(forward_backend())

        receive_queue = asyncio.Queue()
        
        scope = {
            "type": "postgres",
            "client": client_writer.get_extra_info('peername'),
            "params": params
        }

        async def receive():
            return await receive_queue.get()

        async def send(message: dict):
            if message["type"] == "FORWARD":
                backend_writer.write(message["raw"])
                await backend_writer.drain()
            elif message["type"] == "REJECT":
                err_packet = build_postgres_error(message["message"], message.get("code", "42501"))
                client_writer.write(err_packet)
                await client_writer.drain()

        # Fire up Application Task
        app_task = asyncio.create_task(self.app(scope, receive, send))

        # Main Client Binary Packet Loop
        try:
            while True:
                msg_type = await client_reader.read(1)
                if not msg_type: break

                msg_len_bytes = await client_reader.readexactly(4)
                msg_len = struct.unpack('!I', msg_len_bytes)[0]
                body = await client_reader.readexactly(msg_len - 4)
                full_packet = msg_type + msg_len_bytes + body

                event = {"type": "UNKNOWN", "raw": full_packet}

                if msg_type == b'Q':  # Simple Query
                    event["type"] = "QUERY"
                    event["sql"] = body[:-1].decode('utf-8', errors='ignore')
                elif msg_type == b'P': # Extended Protocol Parse
                    parts = body.split(b'\x00')
                    event["type"] = "PARSE"
                    event["sql"] = parts[1].decode('utf-8', errors='ignore') if len(parts) > 1 else ""

                await receive_queue.put(event)
        except Exception:
            pass
        finally:
            await receive_queue.put({"type": "DISCONNECT"})
            backend_task.cancel()
            app_task.cancel()
            client_writer.close()
            backend_writer.close()


server = Server(app_obj=None, host="0.0.0.0", port=8080, db_host="postgresql_db", db_port=5432)
server.run()
