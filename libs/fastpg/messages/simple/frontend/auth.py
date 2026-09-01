from ... import CheckerBuilder, ParserBuilder, MessageBase
from ...checkers import Lenght


class GSSResponse(MessageBase):
    checker = CheckerBuilder().addChar("p").addInt32(Lenght())
    parser = ParserBuilder().addByte("data")

class PasswordMessage(MessageBase):
    checker = CheckerBuilder().addChar("p").addInt32(Lenght())
    parser = ParserBuilder().addString("password")

class SASLInitialResponse(MessageBase):
    checker = CheckerBuilder().addChar("p").addInt32(Lenght())
    parser = ParserBuilder().addString("mechanism").addSequence(
        "payload", 
        ParserBuilder().addInt32("length").addByte("payload"), 
        transform=lambda data: data["payload"][0], 
        retransform=lambda data: {"length": [len(data) if data else -1], "payload": [data]}
        )

class SASLResponse(MessageBase):
    checker = CheckerBuilder().addChar("p").addInt32(Lenght())
    parser = ParserBuilder().addByte("data")
