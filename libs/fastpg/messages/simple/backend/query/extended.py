from .... import CheckerBuilder, ParserBuilder, MessageBase


class ParseComplete(MessageBase):
    checker = CheckerBuilder().addChar("1").addInt32(4)
    parser = ParserBuilder()

class BindComplete(MessageBase):
    checker = CheckerBuilder().addChar("2").addInt32(4)
    parser = ParserBuilder()
