import asyncio
from asyncio import StreamReader
from asyncio import StreamWriter
import struct

from messages.special import StartupMessage, SSLRequest, GSSENCRequest, CancelRequest
from messages.simple.frontend import Query
from messages.simple.frontend.extended_query import Parse, Sync

from messages.simple.backend import ReadyForQuery
from messages.simple.backend.auth import AuthenticationOk

from state_machine import StateMachine
from state_machine.transitions import transitions
from state_machine.states import State
from state_machine.events import Event

from enum import Enum


async def read_special_packet(reader: StreamReader):
    len_bytes = await reader.readexactly(4)
    length = struct.unpack('!I', len_bytes)[0]
    rest = await reader.readexactly(length - 4)
    return len_bytes + rest

async def read_simple_packet(reader: StreamReader):
    msg_type = await reader.read(1)
    if not msg_type: return
    msg_len_bytes = await reader.readexactly(4)
    msg_len = struct.unpack('!I', msg_len_bytes)[0]
    body = await reader.readexactly(msg_len - 4)
    return msg_type + msg_len_bytes + body

async def handle_cancel(id, key):
    pass

async def handle_startup(client_reader, client_writer):
    startup_packet = None
    ssl_negotiated = False
    gssenc_negotiated = False
    while True:
        try:
            startup_packet = await read_special_packet(client_reader)
            if StartupMessage.matches(startup_packet):
                break

            elif SSLRequest.matches(startup_packet):
                if ssl_negotiated:
                    raise ConnectionError("Client sent duplicate SSLRequest")
                client_writer.write(b'N')
                await client_writer.drain()
                ssl_negotiated = True

            elif GSSENCRequest.matches(startup_packet):
                if gssenc_negotiated:
                    raise ConnectionError("Client sent duplicate GSSENCRequest")
                client_writer.write(b'N')
                await client_writer.drain()
                gssenc_negotiated = True

            elif CancelRequest.matches(startup_packet):
                cancel_req = CancelRequest.parse(startup_packet)
                await handle_cancel(cancel_req["process_ID"][0], cancel_req["secret_key"][0])
                client_writer.close()
                return
            
        except Exception:
            client_writer.close()
            return
        
    return startup_packet

def build_postgres_error(message: str, code: str = "42501") -> bytes:
    fields = [
        b'S' + b'ERROR',
        b'C' + code.encode('utf-8'),
        b'M' + message.encode('utf-8'),
        b'\x00'
    ]
    payload = b'\x00'.join(fields)
    return b'E' + struct.pack('!I', 4 + len(payload)) + payload

class Signal(Enum):
    _break = 1

async def loop(client_reader, client_writer, backend_reader, backend_writer, client_callback, backend_callback):
    client_task = asyncio.create_task(read_simple_packet(client_reader))
    backend_task = asyncio.create_task(read_simple_packet(backend_reader))

    while True:
        done, _ = await asyncio.wait(
            [client_task, backend_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        if client_task in done:
            if client_task.result() == None: break
            
            res = await client_callback(backend_writer, client_task.result())
            if res == Signal._break: break
            client_task = asyncio.create_task(read_simple_packet(client_reader))

        if backend_task in done:
            if backend_task.result() == None: break

            res = await backend_callback(client_writer, backend_task.result())
            if res == Signal._break: break
            backend_task = asyncio.create_task(read_simple_packet(backend_reader))

    client_task.cancel()
    backend_task.cancel()

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
            quit()

    async def _handle_connection(self, client_reader: StreamReader, client_writer: StreamWriter):
        state_machine = StateMachine(State.Startup, transitions)

        startup_packet = await handle_startup(client_reader, client_writer)
        params = StartupMessage.parse(startup_packet)
        print(params)

        try:
            backend_reader, backend_writer = await asyncio.open_connection(self.db_host, self.db_port)
            backend_writer.write(startup_packet)
            await backend_writer.drain()
        except Exception as e:
            client_writer.write(build_postgres_error("Database backend unreachable."))
            await client_writer.drain()
            client_writer.close()
            return

        
        async def back_han(client_writer, back_packet):
            client_writer.write(back_packet)
            await client_writer.drain()
            if AuthenticationOk.matches(back_packet):
                return Signal._break

        async def cli_han(backend_writer, front_packet):
            backend_writer.write(front_packet)
            await backend_writer.drain()

        await loop(client_reader, client_writer, backend_reader, backend_writer, cli_han, back_han)

        state_machine.transition(Event.StartupComplete)

        #receive_queue = asyncio.Queue()
        
        #scope = {
        #    "type": "postgres",
        #    "client": client_writer.get_extra_info('peername'),
        #    "params": params
        #}

        #async def receive():
        #    return await receive_queue.get()

        #async def send(message: dict):
        #    if message["type"] == "FORWARD":
        #        backend_writer.write(message["raw"])
        #        await backend_writer.drain()
        #    elif message["type"] == "REJECT":
        #        err_packet = build_postgres_error(message["message"], message.get("code", "42501"))
        #        client_writer.write(err_packet)
        #        await client_writer.drain()

        #app_task = asyncio.create_task(self.app(scope, receive, send))

        async def cli_han(backend_writer, front_packet):
            if state_machine.state == State.Idle:
                
                if Query.matches(front_packet):
                    state_machine.transition(Event.NewSimpleQuery)
                elif Parse.matches(front_packet):
                    state_machine.transition(Event.NewExtendedQuery)
                else:
                    state_machine.transition(Event.UnknowPacket)
    
            if state_machine.state == State.SimpleQuery:
                print(f"Simple Query: {Query.parse(front_packet)}")

                backend_writer.write(front_packet)
                await backend_writer.drain()
                state_machine.transition(Event.EndOfQuery)
    
            elif state_machine.state == State.ExtendedQuery:
                print("Extended Query")

                backend_writer.write(front_packet)
                await backend_writer.drain()
                if Sync.matches(front_packet):
                    state_machine.transition(Event.EndOfQuery)

            elif state_machine.state == State.Unknow:
                backend_writer.write(front_packet)
                await backend_writer.drain()
                
        async def back_han(client_writer, back_packet):
            if state_machine.state == State.Idle:
                state_machine.transition(Event.UnknowPacket)
            
            if state_machine.state == State.QueryResponse:
                client_writer.write(back_packet)
                await client_writer.drain()
                if ReadyForQuery.matches(back_packet):
                    state_machine.transition(Event.ReadyForQuery)
    
            elif state_machine.state == State.Unknow:
                client_writer.write(back_packet)
                await client_writer.drain()
                if ReadyForQuery.matches(back_packet):
                    state_machine.transition(Event.ReadyForQuery)

        await loop(client_reader, client_writer, backend_reader, backend_writer, cli_han, back_han)
    
        client_writer.close()
        backend_writer.close()

if __name__ == "__main__":
    #server = Server(app_obj=None, host="0.0.0.0", port=8080, db_host="postgresql_db", db_port=5432)
    server = Server(app_obj=None, host="0.0.0.0", port=8080, db_host="0.0.0.0", db_port=5432)
    server.run()
