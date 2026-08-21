from ... import CheckerBuilder, ParserBuilder, MessageBase
from ...checkers import TrueChecker
from ...extensions import CountLists


class Parse(MessageBase):
    checker = CheckerBuilder().addChar("P").addInt32(TrueChecker())
    parser = ParserBuilder().addString("statement").addString("query").addSequence(
        "OID_param_types", ParserBuilder()
        .addInt16("num")
        .addInt32("OID_type", count=lambda ctx: ctx.decoded["num"][-1]),
        transform=lambda data: data["OID_type"]
        )

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

class Describe(MessageBase):
    checker = CheckerBuilder().addChar("D").addInt32(TrueChecker())
    parser = ParserBuilder().addChar("S_or_P").addString("name_of_prepared")

class Execute(MessageBase):
    checker = CheckerBuilder().addChar("E").addInt32(TrueChecker())
    parser = ParserBuilder().addString("portal_to_execute").addInt32("max_return_row_num")

class Sync(MessageBase):
    checker = CheckerBuilder().addChar("S").addInt32(4)
    parser = ParserBuilder()
