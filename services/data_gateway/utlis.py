import io
import asyncio

class AsyncStreamIterator(io.RawIOBase):
    def __init__(self, async_stream, loop):
        self.async_stream = async_stream
        self.loop = loop
        self.buffer = bytearray()

    def readable(self):
        return True

    def readinto(self, b):
        if not self.buffer:
            try:
                chunk = asyncio.run_coroutine_threadsafe(
                    self.async_stream.__anext__(), self.loop
                ).result()
                self.buffer.extend(chunk)
            except StopAsyncIteration:
                return 0

        bytes_to_read = min(len(b), len(self.buffer))
        b[:bytes_to_read] = self.buffer[:bytes_to_read]
        del self.buffer[:bytes_to_read]
        return bytes_to_read
