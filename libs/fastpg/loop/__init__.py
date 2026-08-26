from enum import Enum
import asyncio
from messages.readers import read_simple_packet
from asyncio import StreamReader
from asyncio import StreamWriter
from typing import Callable, Any
from inspect import signature, Signature, Parameter


class Ctx:
    def __getattr__(self, name: str) -> Any:
        try:
            return self.__dict__[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name: str, value: Any) -> None:
        self.__dict__[name] = value

    def __delattr__(self, name: str) -> None:
        try:
            del self.__dict__[name]
        except KeyError:
            raise AttributeError(name) from None
    
    def __getitem__(self, name: str) -> Any:
        try:
            return self.__dict__[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setitem__(self, name: str, value: Any) -> None:
        self.__dict__[name] = value

    def __delitem__(self, name: str) -> None:
        try:
            del self.__dict__[name]
        except KeyError:
            raise AttributeError(name) from None

    def get(self, name: str, default: Any | None = None) -> Any:
        return self.__dict__.get(name, default)

    def pop(self, name: str) -> Any:
        return self.__dict__.pop(name)

class Signal(Enum):
    _break = 1

def kwargs(sig: Signature, args: list) -> dict:
    result = {}
    types = {type(arg): arg for arg in args}
    for name, param in sig.parameters.items():
        if param.annotation != Parameter.empty and param.annotation in types:
            result[name] = types[param.annotation]   
    return result

async def loop(
        frontend_reader: StreamReader,
        frontend_writer: StreamWriter,
        frontend_callback: Callable,

        backend_reader: StreamReader,
        backend_writer: StreamWriter,
        backend_callback: Callable
        ):
    client_task = asyncio.create_task(read_simple_packet(frontend_reader))
    backend_task = asyncio.create_task(read_simple_packet(backend_reader))

    frontend_sig = signature(frontend_callback)
    backend_sig = signature(backend_callback)

    frontend_ctx = Ctx()
    backend_ctx = Ctx()

    while True:
        done, _ = await asyncio.wait(
            [client_task, backend_task],
            return_when=asyncio.FIRST_COMPLETED
        )

        if client_task in done:
            if client_task.result() == None: break

            res = await frontend_callback(**kwargs(frontend_sig, [backend_writer, client_task.result(), frontend_ctx]))
            if res == Signal._break: break
            client_task = asyncio.create_task(read_simple_packet(frontend_reader))

        if backend_task in done:
            if backend_task.result() == None: break

            res = await backend_callback(**kwargs(backend_sig, [frontend_writer, backend_task.result(), backend_ctx]))
            if res == Signal._break: break
            backend_task = asyncio.create_task(read_simple_packet(backend_reader))

    client_task.cancel()
    backend_task.cancel()