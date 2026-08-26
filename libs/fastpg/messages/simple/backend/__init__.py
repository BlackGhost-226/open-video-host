from ... import CheckerBuilder, ParserBuilder, MessageBase
from ...checkers import TrueChecker
from ...extensions import UntilNullLists


class BackendKeyData(MessageBase):
    checker = CheckerBuilder().addChar("K").addInt32(TrueChecker())
    parser = ParserBuilder().addInt32("process_id").addByte("secret_key")

class CloseComplete(MessageBase):
    checker = CheckerBuilder().addChar("3").addInt32(4)
    parser = ParserBuilder()

class CommandComplete(MessageBase):
    checker = CheckerBuilder().addChar("C").addInt32(TrueChecker())
    parser = ParserBuilder().addString("command_tag")

class FunctionCallResponse(MessageBase):
    checker = CheckerBuilder().addChar("V").addInt32(TrueChecker())
    parser = ParserBuilder().addInt32("len", unsigned=False).addByte("result_value", length=lambda ctx: ctx.decoded["len"][-1], condition=lambda ctx: ctx.decoded["len"][-1] != -1, default=None)

class NoData(MessageBase):
    checker = CheckerBuilder().addChar("n").addInt32(4)
    parser = ParserBuilder()

class ParameterDescription(MessageBase):
    checker = CheckerBuilder().addChar("t").addInt32(TrueChecker())
    parser = ParserBuilder().addInt16("parameter_num").addInt32("object_ids", count=lambda ctx: ctx.decoded["parameter_num"][-1])

class ParameterStatus(MessageBase):
    checker = CheckerBuilder().addChar("S").addInt32(TrueChecker())
    parser = ParserBuilder().addString("run_time_param").addString("param_value")

class PortalSuspended(MessageBase):
    checker = CheckerBuilder().addChar("s").addInt32(4)
    parser = ParserBuilder()

class ReadyForQuery(MessageBase):
    checker = CheckerBuilder().addChar("Z").addInt32(5)
    parser = ParserBuilder().addChar("transaction_status")

from .query import *
from .query.extended import *
from .auth import *
from .copy import *
from .info import *

allMessages = [
    RowDescription, 
    DataRow, 
    EmptyQueryResponse, 
    AuthenticationCleartextPassword, 
    AuthenticationGSS, 
    AuthenticationGSSContinue, 
    AuthenticationKerberosV5, 
    AuthenticationMD5Password, 
    AuthenticationOk, 
    AuthenticationSASL, 
    AuthenticationSASLContinue, 
    AuthenticationSASLFinal, 
    AuthenticationSSPI, 
    ParseComplete, 
    BindComplete, 
    CopyBothResponse, 
    CopyInResponse, 
    CopyOutResponse, 
    ErrorResponse, 
    NoticeResponse, 
    NotificationResponse,
    BackendKeyData,
    CloseComplete,
    CommandComplete,
    FunctionCallResponse,
    NoData,
    ParameterDescription,
    ParameterStatus,
    PortalSuspended,
    ReadyForQuery
    ]
