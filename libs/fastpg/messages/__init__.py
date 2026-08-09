import struct
from dataclasses import dataclass
from typing import Callable, Any
from abc import ABC, abstractmethod
from types import MethodType


NO_VALUE = object()

@dataclass
class Feature:
    min_length: int
    name: str
    callback: Callable
    count: Callable | int = 1
    condition: Callable | None = None
    transform: Callable | None = None
    default: Any = NO_VALUE
    break_condition: Callable | None = None

@dataclass
class CallContext:
    data: bytes
    decoded: dict

class Builder(ABC):
    def __init__(self, *extensions):
        self.features: list[Feature] = []
        self._total_len = None
        for ext in extensions:
            ext_obj = ext().funcs
            for func in ext_obj:
                setattr(self, func.__name__, MethodType(func.__func__, self))

    @property
    def min_len(self):
        if self._total_len != None:
            return self._total_len
        t_len = 0
        for i in self.features:
            t_len = t_len + abs(i.min_length)
        self._total_len = t_len
        return t_len

    def addChar(self, name: str, **kwargs) -> "Builder":
        def _parse(ctx: CallContext) -> tuple[str, int]:
            data = ctx.data[:1]
            parsed_data = struct.unpack("!c", data)[0].decode("utf-8", errors="ignore")
            return parsed_data, 1
        
        self.features.append(Feature(1, name, _parse, **kwargs))
        return self
    
    def addInt32(self, name: str, unsigned: bool = True, **kwargs) -> "Builder":
        def _parse(ctx: CallContext) -> tuple[int, int]:
            data = ctx.data[:4]
            format_str = "!I" if unsigned else "!i"
            parsed_data = struct.unpack(format_str, data)[0]
            return parsed_data, 4
        
        self.features.append(Feature(4, name, _parse, **kwargs))
        return self

    def addInt16(self, name: str, unsigned: bool = True, **kwargs) -> "Builder":
        def _parse(ctx: CallContext) -> tuple[int, int]:
            data = ctx.data[:2]
            format_str = "!H" if unsigned else "!h"
            parsed_data = struct.unpack(format_str, data)[0]
            return parsed_data, 2
        
        self.features.append(Feature(2, name, _parse, **kwargs))
        return self

    def addInt8(self, name: str, unsigned: bool = True, **kwargs) -> "Builder":
        def _parse(ctx: CallContext) -> tuple[int, int]:
            data = ctx.data[:1]
            format_str = "!B" if unsigned else "!b"
            parsed_data = struct.unpack(format_str, data)[0]
            return parsed_data, 1
        
        self.features.append(Feature(1, name, _parse, **kwargs))
        return self
    
    def addString(self, name: str, **kwargs) -> "Builder":
        def _parse(ctx: CallContext) -> tuple[str, int]:
            data = ctx.data
            null_idx = data.find(b'\x00')
            if null_idx == -1:
                return data.decode('utf-8', errors='ignore'), len(data)
            return data[:null_idx].decode('utf-8', errors='ignore'), null_idx + 1
        
        self.features.append(Feature(-1, name, _parse, **kwargs))
        return self

    def addByte(self, name: str, length: Callable | int = -1, **kwargs) -> "Builder":
        g_length = length

        def _parse(ctx: CallContext) -> tuple[bytes, int]:
            if isinstance(g_length, Callable):
                length = g_length(ctx)
            else:
                length = g_length

            if length != -1:
                return ctx.data[:length], length
            else:
                return ctx.data, len(ctx.data)
        
        self.features.append(Feature(-1, name, _parse, **kwargs))
        return self

    def addSequence(self, name: str, builder: "Builder", **kwargs) -> "Builder":
        self.features.append(Feature(builder.min_len, name, builder.decode, **kwargs))
        return self

    @abstractmethod
    def decode(self, payload_data: bytes):
        pass

class ParserBuilder(Builder):
    def decode(self, payload_data: bytes):
        offset = 0
        decoded = {}
        for feature in self.features:
            if feature.condition and not feature.condition(CallContext(payload_data[offset:], decoded)):
                if feature.default != NO_VALUE:
                    decoded[feature.name] = [feature.default]
                continue

            count = feature.count(CallContext(payload_data[offset:], decoded)) if isinstance(feature.count, Callable) else feature.count 
            data_list = []
            for _ in range(count if count != -1 else len(payload_data[offset:])):
                if offset >= len(payload_data):
                    break

                if feature.break_condition and feature.break_condition(CallContext(payload_data[offset:], decoded)):
                    break

                data = feature.callback(CallContext(payload_data[offset:], decoded))
                offset = offset + data[1]
                data = feature.transform(data[0]) if feature.transform else data[0]
                data_list.append(data)
            decoded[feature.name] = data_list
        return decoded, offset

class CheckerBuilder(Builder):
    def decode(self, payload_data: bytes):
        feature_len = self.min_len

        if not isinstance(payload_data, (bytes, bytearray)) or len(payload_data) < feature_len:
            return False

        offset = 0
        for feature in self.features:
            data = feature.callback(CallContext(payload_data[offset:], {}))
            offset = offset + data[1]
            if not feature.name == data[0]:
                return False

        return True

    def __eq__(self, packet: bytes):
        return self.decode(packet)
    
class MessageBase(ABC):
    checker: CheckerBuilder = None
    parser: ParserBuilder = None
    @classmethod
    def parse(cls, packet: bytes):
        return cls.parser.decode(packet[cls.checker.min_len:])[0]

    @classmethod
    def matches(cls, packet: bytes) -> bool:
        return cls.checker == packet if cls.checker else False

class BuilderExtension(ABC):
    def __init__(self):
        self.funcs = [getattr(self, method) for method in dir(self) if callable(getattr(self, method)) and not method.startswith("__")]
