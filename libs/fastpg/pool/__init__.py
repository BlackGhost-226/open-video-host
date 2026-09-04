from dataclasses import dataclass
from asyncio import StreamReader, StreamWriter, Lock, Task, create_task, gather, open_connection
from typing import Callable

from messages import MessageBase
from messages.special import StartupMessage
from messages.simple.backend.auth import AuthenticationCleartextPassword, AuthenticationSASL
from messages.readers import read_simple_packet

from .auth import clear_text, sasl
from .errors import InterfaceError, Warning
from .async_list import AsyncList


@dataclass
class Resource:
    reader: StreamReader
    writer: StreamWriter

@dataclass
class ConnectionOptions:
    host: str
    port: int
    credentials_callback: Callable[[], tuple[str, str]]


class Pool:
    def __init__(self, connection_options: ConnectionOptions, max: int = 3, min: int = 1):
        self.auth_options: list[tuple[MessageBase, Callable[[StreamReader, StreamWriter, str, bytes], bool]]] = [
            (AuthenticationCleartextPassword, clear_text),
            (AuthenticationSASL, sasl)
            ]
        self.connection_options: ConnectionOptions = connection_options

        self._buf: AsyncList[Resource] = AsyncList()
        self._lock = Lock()

        self._fill_task: Task = None

        self._max = max
        self._min = min

        self.closed: bool = False
        self._closing: bool = False

    @property
    def size(self):
        return len(self._buf)

    async def _monitor_levels(self):
        async with self._lock:
            should_buffer = (
                len(self._buf) < self._min
                and not self._closing
                and self._fill_task is None
            )

        if should_buffer:
            create_task(self._buffer(fill_to_min=True))

    async def _buffer(self, fill_to_min: bool = False):
        async with self._lock:
            if self._fill_task is not None:
                existing = self._fill_task
            else:
                target = self._min if fill_to_min else self._max
                amount = target - len(self._buf)
                if amount < 1:
                    return

                task = create_task(self._buffer_impl(amount))
                self._fill_task = task
                existing = task

        await existing

    async def _buffer_impl(self, amount: int):
        try:
            tasks = [
                create_task(self._connect())
                for _ in range(amount)
            ]

            results = await gather(
                *tasks,
                return_exceptions=True,
            )

            for result in results:
                if isinstance(result, Exception):
                    raise result

        finally:
            async with self._lock:
                self._fill_task = None


    async def _connect(self):
        reader, writer = await open_connection(self.connection_options.host, self.connection_options.port)
        await self._startup(reader, writer)
        await self._buf.put(Resource(reader, writer))

    async def _startup(self, reader: StreamReader, writer: StreamWriter):
            user, passwd = self.connection_options.credentials_callback()
            start_pkt = StartupMessage.build({'parameters': [{"user": [user], "database": [user], "application_name": ["fastpg_pooler"], "client_encoding": ["UTF8"]}]})
            writer.write(start_pkt)
            await writer.drain()
    
            pkt = await read_simple_packet(reader)
            succeeded = False
            for option in self.auth_options:
                if option[0].matches(pkt):
                    succeeded = await option[1](reader, writer, passwd, pkt)
                    break
            if not succeeded:
                raise InterfaceError("Cannot authenticate into the database because the database's authentication method is not supported.")

    async def _disconnect(self, resource: Resource):
        writer = resource.writer
        writer.close()
        await writer.wait_closed()

    async def _check_connection(self, resource: Resource):
        return True

    async def _reset_connection(self, resource: Resource):
        pass


    async def start(self):
        if self.closed:
            raise Warning("The connection pool is closed")
        await self._buffer()

    async def close(self):
        if self.closed:
            raise Warning("The connection pool is closed")
        async with self._lock:
            if not self.closed:
                self._closing = True
                for _ in range(len(self._buf)):
                    await self._disconnect(self._buf.pop())
                self.closed = True
                self._closing = False

    async def get(self) -> Resource:
        if self.closed:
            raise Warning("The connection pool is closed")

        resource = await self._buf.get()
        await self._monitor_levels()
        return resource

    async def put(self, resource: Resource):
        if self.closed:
            await self._disconnect(resource)
            # raise Warning("The connection pool is closed")

        async with self._lock:
            if any(resource is existing for existing in self._buf):
                raise TypeError("Cannot 'put' duplicate value.")
            
            if len(self._buf) >= self._max or self._closing:
                should_destroy = True
            else:
                should_destroy = False

        if not await self._check_connection(resource) and should_destroy == False:
            should_destroy = True

        if should_destroy:
            await self._disconnect(resource)
            return

        await self._reset_connection(resource)
        await self._buf.put(resource)
