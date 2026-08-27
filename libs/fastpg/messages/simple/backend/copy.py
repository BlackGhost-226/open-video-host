from ... import CheckerBuilder, ParserBuilder, MessageBase
from ...checkers import Lenght


class CopyInResponse(MessageBase):
    checker = CheckerBuilder().addChar("G").addInt32(Lenght())
    parser = ParserBuilder().addInt8("overall_format").addInt16("column_num").addInt16("column_formats", count=lambda ctx: ctx.decoded["column_num"][-1])

class CopyOutResponse(MessageBase):
    checker = CheckerBuilder().addChar("H").addInt32(Lenght())
    parser = ParserBuilder().addInt8("overall_format").addInt16("column_num").addInt16("column_formats", count=lambda ctx: ctx.decoded["column_num"][-1])

class CopyBothResponse(MessageBase):
    checker = CheckerBuilder().addChar("W").addInt32(Lenght())
    parser = ParserBuilder().addInt8("overall_format").addInt16("column_num").addInt16("column_formats", count=lambda ctx: ctx.decoded["column_num"][-1])
