from ... import CheckerBuilder, ParserBuilder, MessageBase
from ...checkers import TrueChecker
from ...extensions import CountLists


class Close(MessageBase):
    checker = CheckerBuilder().addChar("C").addInt32(TrueChecker())
    parser = ParserBuilder().addChar("S_or_P").addString("name_of_prepared")

class CopyFail(MessageBase):
    checker = CheckerBuilder().addChar("f").addInt32(TrueChecker())
    parser = ParserBuilder().addString("error_message")

class Flush(MessageBase):
    checker = CheckerBuilder().addChar("H").addInt32(4)
    parser = ParserBuilder()

class FunctionCall(MessageBase):
    checker = CheckerBuilder().addChar("F").addInt32(TrueChecker())
    parser = (ParserBuilder()
              .addInt32("OID")
              .addSequence("format_codes", ParserBuilder()
                .addInt16("format_code_num")
                .addInt16("format_codes", count=lambda ctx: ctx.decoded["format_code_num"][-1]),
                transform=lambda data: data["format_codes"]
              )
              .addSequence("arguments", ParserBuilder(CountLists)
                .addInt16("num")
                .addIntByteList("argument", "num"),
                transform=lambda data: data["argument"]
              )
              .addInt16("result_format_code")
              )

class Query(MessageBase):
    checker = CheckerBuilder().addChar("Q").addInt32(TrueChecker())
    parser = ParserBuilder().addString("query")

class Terminate(MessageBase):
    checker = CheckerBuilder().addChar("X").addInt32(4)
    parser = ParserBuilder()
