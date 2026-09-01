import time
from .errors import DataError
import datetime


def Date(year: int, month: int, day: int) -> datetime.date:
    try:
        return datetime.date(year, month, day)
    except (TypeError, ValueError) as e:
        raise DataError(f"Invalid date values: {e}") from e

def Time(hour: int, minute: int, second: int = 0, microsecond: int = 0) -> datetime.time:
    try:
        return datetime.time(hour, minute, second, microsecond)
    except (TypeError, ValueError) as e:
        raise DataError(f"Invalid time values: {e}") from e

def Timestamp(
    year: int, 
    month: int, 
    day: int, 
    hour: int = 0, 
    minute: int = 0, 
    second: int = 0, 
    microsecond: int = 0
) -> datetime.datetime:
    try:
        return datetime.datetime(year, month, day, hour, minute, second, microsecond)
    except (TypeError, ValueError) as e:
        raise DataError(f"Invalid timestamp values: {e}") from e

def DateFromTicks(ticks):
    return Date(*time.localtime(ticks)[:3])

def TimeFromTicks(ticks):
    return Time(*time.localtime(ticks)[3:6])

def TimestampFromTicks(ticks):
    return Timestamp(*time.localtime(ticks)[:6])

def Binary(string: str | bytes) -> bytes:
    if isinstance(string, bytes):
        return string.decode("utf-8", errors="ignore").encode("ascii", errors="ignore")
    elif isinstance(string, str):
        return string.encode("ascii", errors="ignore")
    raise DataError(f"Binary constructor requires str or bytes, got {type(string).__name__}")
