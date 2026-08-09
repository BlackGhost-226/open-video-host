from ... import CheckerBuilder, ParserBuilder, MessageBase
from ...checkers import TrueChecker


class SASLInitialResponse(MessageBase):
    checker = CheckerBuilder().addChar("p").addInt32(TrueChecker())
    parser = ParserBuilder().addString("mechanism").addInt32("length").addByte("payload")

class Query(MessageBase):
    checker = CheckerBuilder().addChar("Q").addInt32(TrueChecker())
    parser = ParserBuilder().addString("query")
