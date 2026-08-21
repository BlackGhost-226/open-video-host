from ... import CheckerBuilder, ParserBuilder, MessageBase
from ...checkers import TrueChecker


class CopyInResponse(MessageBase):
    checker = CheckerBuilder().addChar("G").addInt32(TrueChecker())
    parser = ParserBuilder().addInt8("overall_format").addInt16("column_num").addInt16("column_formats", count=lambda ctx: ctx.decoded["column_num"][-1])

class CopyOutResponse(MessageBase):
    checker = CheckerBuilder().addChar("H").addInt32(TrueChecker())
    parser = ParserBuilder().addInt8("overall_format").addInt16("column_num").addInt16("column_formats", count=lambda ctx: ctx.decoded["column_num"][-1])

class CopyBothResponse(MessageBase):
    checker = CheckerBuilder().addChar("W").addInt32(TrueChecker())
    parser = ParserBuilder().addInt8("overall_format").addInt16("column_num").addInt16("column_formats", count=lambda ctx: ctx.decoded["column_num"][-1])
