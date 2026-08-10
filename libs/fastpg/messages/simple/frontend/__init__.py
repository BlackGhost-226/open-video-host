from ... import CheckerBuilder, ParserBuilder, MessageBase
from ...checkers import TrueChecker
from ...extensions import UntilNullLists, CountLists

class Bind(MessageBase):
    checker = CheckerBuilder().addChar("B").addInt32(TrueChecker())
    parser = (ParserBuilder()
              .addString("destination_portal")
              .addString("prepared_statement")

              .addSequence("format_codes", ParserBuilder()
                .addInt16("param_format_code_num")
                .addInt16("format_codes", count=lambda ctx: ctx.decoded["param_format_code_num"][-1]),
                transform=lambda data: data["format_codes"]
              )
              .addSequence("parameters", ParserBuilder(CountLists)
                .addInt16("param_num")
                .addIntByteList("parameters", "param_num"),
                transform=lambda data: data["parameters"]
              )
              .addSequence("result_format_codes", ParserBuilder()
                .addInt16("result_format_code_num")
                .addInt16("result_format_codes", count=lambda ctx: ctx.decoded["result_format_code_num"][-1]),
                transform=lambda data: data["result_format_codes"]
              )
              )

class Close(MessageBase):
    checker = CheckerBuilder().addChar("C").addInt32(TrueChecker())
    parser = ParserBuilder().addChar("S_or_P").addString("name_of_prepared")

class CopyFail(MessageBase):
    checker = CheckerBuilder().addChar("f").addInt32(TrueChecker())
    parser = ParserBuilder().addString("error_message")

class Describe(MessageBase):
    checker = CheckerBuilder().addChar("D").addInt32(TrueChecker())
    parser = ParserBuilder().addChar("S_or_P").addString("name_of_prepared")

class Execute(MessageBase):
    checker = CheckerBuilder().addChar("E").addInt32(TrueChecker())
    parser = ParserBuilder().addString("portal_to_execute").addInt32("max_return_row_num")

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

class GSSResponse(MessageBase):
    checker = CheckerBuilder().addChar("p").addInt32(TrueChecker())
    parser = ParserBuilder().addByte("data")

class Parse(MessageBase):
    checker = CheckerBuilder().addChar("P").addInt32(TrueChecker())
    parser = ParserBuilder().addString("statement").addString("query").addSequence(
        "OID_param_types", ParserBuilder()
        .addInt16("num")
        .addInt32("OID_type", count=lambda ctx: ctx.decoded["num"][-1]),
        transform=lambda data: data["OID_type"]
        )

class PasswordMessage(MessageBase):
    checker = CheckerBuilder().addChar("p").addInt32(TrueChecker())
    parser = ParserBuilder().addString("password")

class Query(MessageBase):
    checker = CheckerBuilder().addChar("Q").addInt32(TrueChecker())
    parser = ParserBuilder().addString("query")

class SASLInitialResponse(MessageBase):
    checker = CheckerBuilder().addChar("p").addInt32(TrueChecker())
    parser = ParserBuilder().addString("mechanism").addInt32("length").addByte("payload")

class SASLResponse(MessageBase):
    checker = CheckerBuilder().addChar("p").addInt32(TrueChecker())
    parser = ParserBuilder().addByte("data")

class Sync(MessageBase):
    checker = CheckerBuilder().addChar("S").addInt32(4)
    parser = ParserBuilder()

class Terminate(MessageBase):
    checker = CheckerBuilder().addChar("X").addInt32(4)
    parser = ParserBuilder()
