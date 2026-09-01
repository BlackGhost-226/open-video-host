# https://www.postgresql.org/docs/current/protocol-message-formats.html#PROTOCOL-MESSAGE-FORMATS-NOTICERESPONSE

import struct
from dataclasses import dataclass
from typing import Callable, Any
from abc import ABC, abstractmethod
from types import MethodType

from .checkers import Lenght, LSbChecker, MSbChecker, TrueChecker


NO_VALUE = object()

@dataclass
class Feature:
    min_length: int
    name: str
    callback: Callable
    encode_callback: Callable
    count: Callable | int = 1
    condition: Callable | None = None
    transform: Callable | None = None
    retransform: Callable | None = None
    default: Any = NO_VALUE
    break_condition: Callable | None = None

    def __post_init__(self):
        if self.transform is not None and self.retransform is None:
            raise RuntimeError("If transform is used, retransform is required")

@dataclass
class CallContext:
    data: Any
    decoded: dict | bytes

class Builder(ABC):
    def __init__(self, *extensions):
        self.features: list[Feature] = []
        self._total_len = None
        for ext in extensions:
            ext_obj = ext().funcs
            for func in ext_obj:
                setattr(self, func.__name__, MethodType(func.__func__, self))

    @property
    def min_len(self) -> int:
        if self._total_len != None:
            return self._total_len
        t_len = 0
        for i in self.features:
            t_len = t_len + abs(i.min_length)
        self._total_len = t_len
        return t_len

    def clacRestMinLenght(self, feature: Feature) -> int:
        lenght = int()
        for i in range(self.features.index(feature), len(self.features)):
            lenght = lenght + abs(self.features[i].min_length)
        return lenght

    def addChar(self, name: str, **kwargs) -> "Builder":
        def _parse(ctx: CallContext) -> tuple[str, int]:
            data = ctx.data[:1]
            parsed_data = struct.unpack("!c", data)[0].decode("utf-8", errors="ignore")
            return parsed_data, 1

        def _encode(ctx: CallContext) -> tuple[bytes, int]:
            data = ctx.data[0]
            encoded_data = struct.pack("!c", data.encode("ascii", errors="ignore"))
            return encoded_data, 1
        
        self.features.append(Feature(1, name, _parse, _encode, **kwargs))
        return self
    
    def addInt32(self, name: str, unsigned: bool = True, **kwargs) -> "Builder":
        def _parse(ctx: CallContext) -> tuple[int, int]:
            data = ctx.data[:4]
            format_str = "!I" if unsigned else "!i"
            parsed_data = struct.unpack(format_str, data)[0]
            return parsed_data, 4

        def _encode(ctx: CallContext):
            data = ctx.data
            format_str = "!I" if unsigned else "!i"
            encoded_data = struct.pack(format_str, data)
            return encoded_data, 4
        
        self.features.append(Feature(4, name, _parse, _encode, **kwargs))
        return self

    def addInt16(self, name: str, unsigned: bool = True, **kwargs) -> "Builder":
        def _parse(ctx: CallContext) -> tuple[int, int]:
            data = ctx.data[:2]
            format_str = "!H" if unsigned else "!h"
            parsed_data = struct.unpack(format_str, data)[0]
            return parsed_data, 2

        def _encode(ctx: CallContext):
            data = ctx.data
            format_str = "!H" if unsigned else "!h"
            encoded_data = struct.pack(format_str, data)
            return encoded_data, 2
        
        self.features.append(Feature(2, name, _parse, _encode, **kwargs))
        return self

    def addInt8(self, name: str, unsigned: bool = True, **kwargs) -> "Builder":
        def _parse(ctx: CallContext) -> tuple[int, int]:
            data = ctx.data[:1]
            format_str = "!B" if unsigned else "!b"
            parsed_data = struct.unpack(format_str, data)[0]
            return parsed_data, 1

        def _encode(ctx: CallContext):
            data = ctx.data
            format_str = "!B" if unsigned else "!b"
            encoded_data = struct.pack(format_str, data)
            return encoded_data, 1
        
        self.features.append(Feature(1, name, _parse, _encode, **kwargs))
        return self
    
    def addString(self, name: str, **kwargs) -> "Builder":
        def _parse(ctx: CallContext) -> tuple[str, int]:
            data = ctx.data
            null_idx = data.find(b'\x00')
            if null_idx == -1:
                return data.decode('utf-8', errors='ignore'), len(data)
            return data[:null_idx].decode('utf-8', errors='ignore'), null_idx + 1

        def _encode(ctx: CallContext):
            data = ctx.data
            encoded_data = data.encode("ascii", errors="ignore") + b'\x00'
            return encoded_data, len(encoded_data)
        
        self.features.append(Feature(-1, name, _parse, _encode, **kwargs))
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

        def _encode(ctx: CallContext):
            data = ctx.data
            if not isinstance(data, bytes) and data is not None:
                raise TypeError(f"Got {type(data).__name__} instead of bytes or None")
            return data if data else b'', len(data) if data else -1
        
        self.features.append(Feature(-1, name, _parse, _encode, **kwargs))
        return self

    def addSequence(self, name: str, builder: "Builder", **kwargs) -> "Builder":
        def _parse(ctx: CallContext) -> tuple[Any, int]:
            data = builder.decode(ctx.data)
            return data[0], data[1]

        def _encode(ctx: CallContext):
            data = builder.encode(ctx.data)
            return data[0], data[1]
        
        self.features.append(Feature(builder.min_len, name, _parse, _encode, **kwargs))
        return self

    @abstractmethod
    def decode(self, payload_data: bytes):
        pass

    @abstractmethod
    def encode(self, payload_data: dict):
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

    def encode(self, payload_data: dict):
        encoded = bytes()
        for feature in self.features:
            #print(f"feature.name: {feature.name}")
            #print(f"feature.encode_callback: {feature.encode_callback}")
            #print(f"feature.retransform: {feature.retransform}")
            #print(f"payload_data: {payload_data}")

            data = payload_data.get(feature.name)
            if data == None:
                raise RuntimeError(f"requiered feature missing: {feature.name}")
            #print(f"data: {data}")
            
            for sub_data in data:
                add_data = bytes()
                #print(f"sub_data: {sub_data}")
                
                if feature.retransform:
                    re_data = feature.retransform(sub_data)
                    if isinstance(re_data, tuple):
                        if len(re_data) == 3 and re_data[2]:
                            add_data = re_data[2]

                        if re_data[1] != None:
                            sub_data = {re_data[1]: re_data[0]}
                        else:
                            sub_data = re_data[0]
                    else:
                        sub_data = re_data

                #print(f"sub_data after retransform: {sub_data}")
                #print(f"add_data: {add_data}")
                encoded_data = feature.encode_callback(CallContext(sub_data, payload_data))[0] + add_data
                #print(f"encoded_data: {encoded_data}")
                encoded = encoded + (encoded_data if encoded_data else b'')
                #print(f"encoded: {encoded}")
        return encoded, len(encoded)

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

    def encode(self, payload_data: dict):
        encoded = bytes()
        for feature in self.features:
            data = bytes()
            #print(f"feature.name: {feature.name}")
            #print(f"feature.encode_callback: {feature.encode_callback}")
            #print(f"payload_data: {payload_data}")

            if type(feature.name) == Lenght:
                data = payload_data.get("len") + (self.clacRestMinLenght(feature))
                if data == None:
                    raise RuntimeError(f"requiered feature missing: len")
            elif type(feature.name) == LSbChecker:
                data = feature.name.LSb
            elif type(feature.name) == MSbChecker:
                data = feature.name.MSb
            elif type(feature.name) == TrueChecker:
                encoded = encoded + b'\x00' * abs(feature.min_length)
                continue
            else:
                data = feature.name

            #print(f"data: {data}")
            encoded = encoded + feature.encode_callback(CallContext(data, {}))[0]
            #print(f"encoded: {encoded}")
        return encoded, len(encoded)

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

    @classmethod
    def build(cls, payload: dict):
        par_res = cls.parser.encode(payload)
        return cls.checker.encode({"len": par_res[1]})[0] + par_res[0]

class BuilderExtension(ABC):
    def __init__(self):
        self.funcs = [getattr(self, method) for method in dir(self) if callable(getattr(self, method)) and not method.startswith("__")]
