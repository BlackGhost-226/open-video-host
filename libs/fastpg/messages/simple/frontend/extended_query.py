from ... import CheckerBuilder, ParserBuilder, MessageBase
from ...checkers import Lenght
from ...extensions import CountLists


class Parse(MessageBase):
    checker = CheckerBuilder().addChar("P").addInt32(Lenght())
    parser = ParserBuilder().addString("statement").addString("query").addSequence(
        "OID_param_types", ParserBuilder()
        .addInt16("num")
        .addInt32("OID_type", count=lambda ctx: ctx.decoded["num"][-1]),
        transform=lambda data: data["OID_type"],
        retransform=lambda data: {"num": [len(data)], "OID_type": data}
        )

class Bind(MessageBase):
    checker = CheckerBuilder().addChar("B").addInt32(Lenght())
    parser = (ParserBuilder()
              .addString("destination_portal")
              .addString("prepared_statement")

              .addSequence("format_codes", ParserBuilder()
                .addInt16("param_format_code_num")
                .addInt16("format_codes", count=lambda ctx: ctx.decoded["param_format_code_num"][-1]),
                transform=lambda data: data["format_codes"],
                retransform=lambda data: {"param_format_code_num": [len(data)], "format_codes": data}
              )
              .addSequence("parameters", ParserBuilder(CountLists)
                .addInt16("param_num")
                .addIntByteList("parameters", "param_num"),
                transform=lambda data: data["parameters"],
                retransform=lambda data: {"param_num": [len(data)], "parameters": data}
              )
              .addSequence("result_format_codes", ParserBuilder()
                .addInt16("result_format_code_num")
                .addInt16("result_format_codes", count=lambda ctx: ctx.decoded["result_format_code_num"][-1]),
                transform=lambda data: data["result_format_codes"],
                retransform=lambda data: {"result_format_code_num": [len(data)], "result_format_codes": data}
              )
              )

class Describe(MessageBase):
    checker = CheckerBuilder().addChar("D").addInt32(Lenght())
    parser = ParserBuilder().addChar("S_or_P").addString("name_of_prepared")

class Execute(MessageBase):
    checker = CheckerBuilder().addChar("E").addInt32(Lenght())
    parser = ParserBuilder().addString("portal_to_execute").addInt32("max_return_row_num")

class Sync(MessageBase):
    checker = CheckerBuilder().addChar("S").addInt32(4)
    parser = ParserBuilder()
