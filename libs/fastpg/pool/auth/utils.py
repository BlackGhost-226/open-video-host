import stringprep
import unicodedata
from typing import  Any

from messages.readers import read_simple_packet
from messages.simple.backend import ReadyForQuery
from messages.simple.backend.info import ErrorResponse

from asyncio import StreamReader, IncompleteReadError
from ..errors import OperationalError, ProgrammingError


async def wait(reader: StreamReader, error_text: str):
    while True:
        try:
            packet = await read_simple_packet(reader)
        except IncompleteReadError:
            raise OperationalError("DataBase closed the connection")
        else:
            if ReadyForQuery.matches(packet):
                break
            catch_error(packet, error_text)

def catch_error(packet: bytes, error_text: str):
    if ErrorResponse.matches(packet):
        raise ProgrammingError(f"The DataBase reponded with an ErrorResponse while {error_text}: {ErrorResponse.parse(packet)["errors"]}")

def xor(bytes1, bytes2):
    if len(bytes1) != len(bytes2):
        raise ValueError("Byte sequences must be of equal length for XOR operations")
        
    return bytes(b1 ^ b2 for b1, b2 in zip(bytes1, bytes2))

_PROHIBITED = (
    stringprep.in_table_c12,
    stringprep.in_table_c21_c22,
    stringprep.in_table_c3,
    stringprep.in_table_c4,
    stringprep.in_table_c5,
    stringprep.in_table_c6,
    stringprep.in_table_c7,
    stringprep.in_table_c8,
    stringprep.in_table_c9,
)

def saslprep(data: Any, prohibit_unassigned_code_points: bool = True) -> str:
    if not isinstance(data, str):
        return data

    data = "".join(
        "\u0020" if stringprep.in_table_c12(char) else char
        for char in data
        if not stringprep.in_table_b1(char)
    )

    data = unicodedata.ucd_3_2_0.normalize("NFKC", data)
    if not data:
        return ""

    prohibited = (*_PROHIBITED, stringprep.in_table_a1) if prohibit_unassigned_code_points else _PROHIBITED
    for char in data:
        if any(in_table(char) for in_table in prohibited):
            raise ValueError(f"SASLprep: Prohibited character detected: {repr(char)}")

    has_r_or_al = any(stringprep.in_table_d1(c) for c in data)
    has_l = any(stringprep.in_table_d2(c) for c in data)

    if has_r_or_al:
        if has_l:
            raise ValueError("SASLprep: Cannot mix RandALCat and LCat characters")
        if not (stringprep.in_table_d1(data[0]) and stringprep.in_table_d1(data[-1])):
            raise ValueError("SASLprep: First and last characters must be RandALCat")

    return data
