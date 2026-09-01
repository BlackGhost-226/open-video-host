from asyncio import StreamReader, IncompleteReadError
from typing import BinaryIO
import struct

def _readexactly(reader: BinaryIO, n: int) -> bytes:
    chunks = []
    bytes_left = n

    while bytes_left > 0:
        chunk = reader.read(bytes_left)
        if not chunk:
            partial = b"".join(chunks)
            raise IncompleteReadError(partial=partial, expected=n)
        
        chunks.append(chunk)
        bytes_left -= len(chunk)

    return b"".join(chunks)

def sync_read_special_packet(reader: BinaryIO):
    len_bytes = _readexactly(reader, 4)
    length = struct.unpack('!I', len_bytes)[0]
    rest = _readexactly(reader, length - 4)
    return len_bytes + rest

def sync_read_simple_packet(reader: BinaryIO):
    msg_type = reader.read(1)
    if not msg_type: raise IncompleteReadError(partial=msg_type, expected=1)
    msg_len_bytes = _readexactly(reader, 4)
    msg_len = struct.unpack('!I', msg_len_bytes)[0]
    body = _readexactly(reader, msg_len - 4)
    return msg_type + msg_len_bytes + body


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