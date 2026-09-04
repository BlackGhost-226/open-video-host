# https://www.postgresql.org/docs/current/protocol-flow.html

import asyncio
from asyncio import StreamReader
from asyncio import StreamWriter
import struct

from messages.simple.frontend import Query
from messages.simple.frontend import allMessages as allFrontendMessages
from messages.simple.frontend.extended_query import Parse, Sync

from messages.simple.backend import ReadyForQuery, CommandComplete
from messages.simple.backend import allMessages as allBackendMessages
from messages.simple.backend.query import RowDescription, DataRow

from state_machine import StateMachine
from state_machine.transitions import transitions
from state_machine.states import State
from state_machine.events import Event

from loop import loop, Ctx, Signal
from loop.startup import handle_startup
from loop.auth import handle_authentication

from driver.connection import Connection
import driver.type_objects as to

from pool import Pool, ConnectionOptions


def build_postgres_error(message: str, code: str = "42501") -> bytes:
    fields = [
        b'S' + b'ERROR',
        b'C' + code.encode('utf-8'),
        b'M' + message.encode('utf-8'),
        b'\x00'
    ]
    payload = b'\x00'.join(fields)
    return b'E' + struct.pack('!I', 4 + len(payload)) + payload

def mess_print(messages, packet, lable, not_found_lable="Packet"):
    for message in messages:
        if message.matches(packet):
            print(f"({lable}) {message.__name__}: {message.parse(packet)}")
            return
    print(f"({lable}) {not_found_lable}: {packet}")

class Server:
    def __init__(self, app_obj, host: str, port: int, db_host: str, db_port: int):
        self.app = app_obj
        self.host = host
        self.port = port
        self.db_host = db_host
        self.db_port = db_port

        self.pooler: Pool = None

    def run(self):
        #uvloop.install()
        Connection(f"postgresql://root:abc123@{self.db_host}:{self.db_port}/root").close() # to generate array_map in driver.type_objects
        #print(to.array_map)
        self.pooler = Pool(ConnectionOptions(self.db_host, self.db_port, lambda: ("root", "abc123")))

        async def _main():
            await self.pooler.start()
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

        params = await handle_startup(client_reader, client_writer)
        if params is None:
            client_writer.close()
            await client_writer.wait_closed()
            return
        print(params)

        auth = await handle_authentication(client_reader, client_writer, lambda d: d)
        if auth is None:
            client_writer.close()
            await client_writer.wait_closed()
            return
        print(auth)

        rw = await self.pooler.get()
        backend_reader, backend_writer = (rw.reader, rw.writer)

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

        async def cli_han(backend_writer: StreamWriter, front_packet: bytes, ctx: Ctx):
            if state_machine.state == State.Idle:
                
                if Query.matches(front_packet):
                    state_machine.transition(Event.NewSimpleQuery)
                elif Parse.matches(front_packet):
                    state_machine.transition(Event.NewExtendedQuery)
                else:
                    state_machine.transition(Event.UnknowPacket)
    
            if state_machine.state == State.SimpleQuery:
                mess_print(allFrontendMessages, front_packet, "F")

                backend_writer.write(front_packet)
                await backend_writer.drain()
                state_machine.transition(Event.EndOfQuery)
    
            elif state_machine.state == State.ExtendedQuery:
                print(f"Extended Query: {front_packet}")

                backend_writer.write(front_packet)
                await backend_writer.drain()
                if Sync.matches(front_packet):
                    state_machine.transition(Event.EndOfQuery)

            elif state_machine.state == State.Unknow:
                backend_writer.write(front_packet)
                await backend_writer.drain()
                
        async def back_han(client_writer: StreamWriter, back_packet: bytes, ctx: Ctx):
            if state_machine.state == State.Idle:
                state_machine.transition(Event.UnknowPacket)
            
            if state_machine.state == State.QueryResponse:
                mess_print(allBackendMessages, back_packet, "B", "Query Response")

                if ReadyForQuery.matches(back_packet):
                    state_machine.transition(Event.ReadyForQuery)
                
                elif RowDescription.matches(back_packet):
                    ctx.last_rowDesc = RowDescription.parse(back_packet)
                elif DataRow.matches(back_packet):
                    row_dict = {
                        field["field_name"][0]: value 
                        for field, value in zip(ctx.last_rowDesc["fields"], DataRow.parse(back_packet)["values"])
                    }
                    print(f"(B) Data: {row_dict}")
                #elif CommandComplete.matches(back_packet):
                #    del ctx.last_rowDesc

                client_writer.write(back_packet)
                await client_writer.drain()
    
            elif state_machine.state == State.Unknow:
                client_writer.write(back_packet)
                await client_writer.drain()
                if ReadyForQuery.matches(back_packet):
                    state_machine.transition(Event.ReadyForQuery)

        await loop(client_reader, client_writer, cli_han, backend_reader, backend_writer, back_han)

        await self.pooler.put(rw)
        client_writer.close()
        await client_writer.wait_closed()

if __name__ == "__main__":
    #server = Server(app_obj=None, host="0.0.0.0", port=8080, db_host="postgresql_db", db_port=5432)
    server = Server(app_obj=None, host="0.0.0.0", port=8080, db_host="0.0.0.0", db_port=5432)
    server.run()
