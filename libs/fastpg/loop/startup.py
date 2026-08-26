from messages.special import StartupMessage, SSLRequest, GSSENCRequest, CancelRequest
from messages.readers import read_special_packet
from asyncio import StreamReader
from asyncio import StreamWriter


async def handle_cancel(id, key):
    pass

async def handle_startup(client_reader: StreamReader, client_writer: StreamWriter):
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