# These are messages can be sent either by frontend or backend.

from .. import MessageBase, CheckerBuilder, ParserBuilder
from ..checkers import TrueChecker


class CopyData(MessageBase):
    checker = CheckerBuilder().addChar("d").addInt32(TrueChecker())
    parser = ParserBuilder().addByte("data")

class CopyDone(MessageBase):
    checker = CheckerBuilder().addChar("c").addInt32(4)
    parser = ParserBuilder()
