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
    parser = ParserBuilder().addString("mechanism").addInt32("length").addByte("payload")

class SASLResponse(MessageBase):
    checker = CheckerBuilder().addChar("p").addInt32(Lenght())
    parser = ParserBuilder().addByte("data")
