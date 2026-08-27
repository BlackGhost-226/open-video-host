from ... import CheckerBuilder, ParserBuilder, MessageBase
from ...checkers import Lenght
from ...extensions import CountLists


class Close(MessageBase):
    checker = CheckerBuilder().addChar("C").addInt32(Lenght())
    parser = ParserBuilder().addChar("S_or_P").addString("name_of_prepared")

class CopyFail(MessageBase):
    checker = CheckerBuilder().addChar("f").addInt32(Lenght())
    parser = ParserBuilder().addString("error_message")

class Flush(MessageBase):
    checker = CheckerBuilder().addChar("H").addInt32(4)
    parser = ParserBuilder()

class FunctionCall(MessageBase):
    checker = CheckerBuilder().addChar("F").addInt32(Lenght())
    parser = (ParserBuilder()
              .addInt32("OID")
              .addSequence("format_codes", ParserBuilder()
                .addInt16("format_code_num")
                .addInt16("format_codes", count=lambda ctx: ctx.decoded["format_code_num"][-1]),
                transform=lambda data: data["format_codes"],
                retransform=lambda data: {"format_code_num": [len(data)], "format_codes": data}
              )
              .addSequence("arguments", ParserBuilder(CountLists)
                .addInt16("num")
                .addIntByteList("argument", "num"),
                transform=lambda data: data["argument"],
                retransform=lambda data: {"num": [len(data)], "argument": data}
              )
              .addInt16("result_format_code")
              )

class Query(MessageBase):
    checker = CheckerBuilder().addChar("Q").addInt32(Lenght())
    parser = ParserBuilder().addString("query")

class Terminate(MessageBase):
    checker = CheckerBuilder().addChar("X").addInt32(4)
    parser = ParserBuilder()

from .auth import *
from .extended_query import *

allMessages = [
    GSSResponse, 
    PasswordMessage, 
    SASLInitialResponse, 
    SASLResponse, 
    Parse, 
    Bind, 
    Describe, 
    Execute, 
    Sync, 
    Close, 
    CopyFail, 
    Flush, 
    FunctionCall, 
    Query, 
    Terminate
    ]
