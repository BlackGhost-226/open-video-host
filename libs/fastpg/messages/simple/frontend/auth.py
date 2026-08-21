from ... import CheckerBuilder, ParserBuilder, MessageBase
from ...checkers import TrueChecker
from ...extensions import CountLists


class GSSResponse(MessageBase):
    checker = CheckerBuilder().addChar("p").addInt32(TrueChecker())
    parser = ParserBuilder().addByte("data")

class PasswordMessage(MessageBase):
    checker = CheckerBuilder().addChar("p").addInt32(TrueChecker())
    parser = ParserBuilder().addString("password")

class SASLInitialResponse(MessageBase):
    checker = CheckerBuilder().addChar("p").addInt32(TrueChecker())
    parser = ParserBuilder().addString("mechanism").addInt32("length").addByte("payload")

class SASLResponse(MessageBase):
    checker = CheckerBuilder().addChar("p").addInt32(TrueChecker())
    parser = ParserBuilder().addByte("data")
