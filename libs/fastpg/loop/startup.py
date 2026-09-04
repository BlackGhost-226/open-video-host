from messages.special import StartupMessage, SSLRequest, GSSENCRequest, CancelRequest
from messages.readers import read_special_packet
from asyncio import StreamReader
from asyncio import StreamWriter


async def handle_cancel(id, key):
    pass

async def handle_startup(client_reader: StreamReader, client_writer: StreamWriter):
    ssl_negotiated = False
    gssenc_negotiated = False
    while True:
        try:
            startup_packet = await read_special_packet(client_reader)
            if StartupMessage.matches(startup_packet):
                return StartupMessage.parse(startup_packet)["parameters"][0]

            elif SSLRequest.matches(startup_packet):
                if ssl_negotiated:
                    return None
                client_writer.write(b'N')
                await client_writer.drain()
                ssl_negotiated = True

            elif GSSENCRequest.matches(startup_packet):
                if gssenc_negotiated:
                    return None
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
        