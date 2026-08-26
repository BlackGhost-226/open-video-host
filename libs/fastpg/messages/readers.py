from asyncio import StreamReader
import struct


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