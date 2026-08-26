from . import ParserBuilder, BuilderExtension

class UntilNullLists(BuilderExtension):
    def __init__(self):
        super().__init__()

    def addStringList(self, name: str):
        self.addString(name, count=-1, break_condition=lambda ctx: ctx.data[0] == 0, retransform=lambda data: data + "\0") # \0 = null in ascii -> \x00
        return self

    def addIntByteList(self, name: str):
        self.addSequence(
        name, 
        ParserBuilder()
        .addInt32("len", unsigned=False)
        .addByte
        (
            "value", 
            length=lambda ctx: ctx.decoded["len"][-1],
            condition=lambda ctx: ctx.decoded["len"][-1] != -1,
            default=None
        ), 
        count=-1,

        transform=lambda data: data["value"][0],
        retransform=lambda data: {"len": [len(data) if data else -1], "value": [data]},

        break_condition=lambda ctx: ctx.data[0] == 0
        )
        return self

    def addKeyValuePairList(self, name: str):
        self.addSequence(name, ParserBuilder().addSequence(
            "params", 
            ParserBuilder().addString("key").addString("val"), 
            count=-1, 
            break_condition=lambda ctx: ctx.data[0] == 0
            ),
            transform=lambda data: {i["key"][0]: i["val"] for i in data["params"]},
            retransform=lambda data: ([{"key": [key], "val": val} for key, val in data.items()], "params")
            )
        return self

    def addCharValuePairList(self, name: str):
        self.addSequence(name, ParserBuilder().addSequence(
            "params", 
            ParserBuilder().addChar("key").addString("val"), 
            count=-1, 
            break_condition=lambda ctx: ctx.data[0] == 0
            ),
            transform=lambda data: {i["key"][0]: i["val"] for i in data["params"]},
            retransform=lambda data: ([{"key": [key], "val": val} for key, val in data.items()], "params")
            )
        return self

class CountLists(BuilderExtension):
    def __init__(self):
        super().__init__()

    def addStringList(self, name: str, until: str):
        self.addString(name, count=lambda ctx: ctx.decoded[until][-1])
        return self

    def addIntByteList(self, name: str, until: str):
        self.addSequence(
        name, 
        ParserBuilder()
        .addInt32("len", unsigned=False)
        .addByte
        (
            "value", 
            length=lambda ctx: ctx.decoded["len"][-1],
            condition=lambda ctx: ctx.decoded["len"][-1] != -1,
            default=None
        ), 
        count=lambda ctx: ctx.decoded[until][-1],
        transform=lambda data: data["value"][0],
        retransform=lambda data: {"len": [len(data) if data else -1], "value": [data]}
        )
        return self
