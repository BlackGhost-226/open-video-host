from .. import MessageBase, CheckerBuilder, ParserBuilder
from ..checkers import TrueChecker, NoLenTrueChecker
from ..extensions import UntilNullLists

class StartupMessage(MessageBase):
    checker = CheckerBuilder().addInt32(TrueChecker()).addInt16(3).addInt16(NoLenTrueChecker())
    parser = ParserBuilder(UntilNullLists).addKeyValuePairList("parameters")

class SSLRequest(MessageBase):
    checker = CheckerBuilder().addInt32(8).addInt32(80877106)
    parser = ParserBuilder()

class GSSENCRequest(MessageBase):
    checker = CheckerBuilder().addInt32(8).addInt32(80877107)
    parser = ParserBuilder()

class CancelRequest(MessageBase):
    checker = CheckerBuilder().addInt32(TrueChecker()).addInt32(80877102)
    parser = ParserBuilder().addInt32("process_id").addInt32("secret_key")
