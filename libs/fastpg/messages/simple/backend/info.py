from ... import CheckerBuilder, ParserBuilder, MessageBase
from ...checkers import TrueChecker
from ...extensions import UntilNullLists


class ErrorResponse(MessageBase):
    checker = CheckerBuilder().addChar("E").addInt32(TrueChecker())
    parser = ParserBuilder(UntilNullLists).addCharValuePairList("errors")

class NoticeResponse(MessageBase):
    checker = CheckerBuilder().addChar("N").addInt32(TrueChecker())
    parser = ParserBuilder(UntilNullLists).addCharValuePairList("notices")

class NotificationResponse(MessageBase):
    checker = CheckerBuilder().addChar("A").addInt32(TrueChecker())
    parser = ParserBuilder().addInt32("process_id").addString("channel").addString("payload")
