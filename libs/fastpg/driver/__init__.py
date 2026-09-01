import datetime
import decimal
import json
import uuid
from .errors import DataError, OperationalError, ProgrammingError
from asyncio import IncompleteReadError
from messages.readers import sync_read_simple_packet
from messages.simple.backend import ReadyForQuery
from messages.simple.backend.info import ErrorResponse
from typing import BinaryIO


apilevel = "2.0"
threadsafety = 0
paramstyle = "format"

def adapt_params(params):
    adapted_params = []
    for param in params:
        adapted_params.append(adapt_param(param))
    return (i for i in adapted_params)

def adapt_param(param) -> str:
    """
    Adapts a Python object into a PostgreSQL-formatted SQL string literal.
    
    Python -> SQL Parameter Conversion Rules:
    - None          -> NULL
    - bool          -> TRUE / FALSE
    - int, float    -> Raw numeric string
    - Decimal       -> Raw numeric string
    - str           -> E'...' (Escaped string literal)
    - bytes         -> '\\x...' (PostgreSQL BYTEA hex string format)
    - date/time/dt  -> 'YYYY-MM-DD...' (ISO-8601 string literal)
    - dict, list    -> 'json_data'::jsonb
    - UUID          -> 'uuid-string'::uuid
    """
    if param is None:
        return "NULL"

    if isinstance(param, bool):
        return "TRUE" if param else "FALSE"

    if isinstance(param, (int, float, decimal.Decimal)):
        return str(param)

    if isinstance(param, str):
        escaped = param.replace("\\", "\\\\").replace("'", "''")
        return f"E'{escaped}'"

    if isinstance(param, (bytes, bytearray)):
        return f"'\\x{param.hex()}'::bytea"

    if isinstance(param, (datetime.date, datetime.time, datetime.datetime)):
        return f"'{param.isoformat()}'"

    if isinstance(param, datetime.timedelta):
        return f"'{param.total_seconds()} seconds'::interval"

    if isinstance(param, uuid.UUID):
        return f"'{str(param)}'::uuid"

    if isinstance(param, (dict, list)):
        try:
            json_str = json.dumps(param).replace("'", "''")
            return f"'{json_str}'::jsonb"
        except (TypeError, ValueError) as e:
            raise DataError(f"Failed to adapt container parameter to JSON: {e}") from e

    print(param)
    raise DataError(
        f"Cannot adapt parameter of type {type(param).__name__} to PostgreSQL SQL literal."
    )

def wait(reader: BinaryIO, error_text: str):
    while True:
        try:
            packet = sync_read_simple_packet(reader)
        except IncompleteReadError:
            raise OperationalError("DataBase closed the connection")
        finally:
            if ReadyForQuery.matches(packet):
                break
            elif ErrorResponse.matches(packet):
                raise ProgrammingError(f"The DataBase reponded with an ErrorResponse while {error_text}: {ErrorResponse.parse(packet)["errors"]}")
