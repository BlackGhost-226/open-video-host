from ... import CheckerBuilder, ParserBuilder, MessageBase
from ...checkers import TrueChecker
from ...extensions import UntilNullLists, CountLists


class AuthenticationOk(MessageBase):
    checker = CheckerBuilder().addChar("R").addInt32(8).addInt32(0)
    parser = ParserBuilder()

class AuthenticationKerberosV5(MessageBase):
    checker = CheckerBuilder().addChar("R").addInt32(8).addInt32(2)
    parser = ParserBuilder()

class AuthenticationCleartextPassword(MessageBase):
    checker = CheckerBuilder().addChar("R").addInt32(8).addInt32(3)
    parser = ParserBuilder()

class AuthenticationMD5Password(MessageBase):
    checker = CheckerBuilder().addChar("R").addInt32(12).addInt32(5)
    parser = ParserBuilder().addByte("salt", 4)

class AuthenticationGSS(MessageBase):
    checker = CheckerBuilder().addChar("R").addInt32(8).addInt32(7)
    parser = ParserBuilder()

class AuthenticationGSSContinue(MessageBase):
    checker = CheckerBuilder().addChar("R").addInt32(TrueChecker()).addInt32(8)
    parser = ParserBuilder().addByte("auth_data")

class AuthenticationSSPI(MessageBase):
    checker = CheckerBuilder().addChar("R").addInt32(8).addInt32(9)
    parser = ParserBuilder()

class AuthenticationSASL(MessageBase):
    checker = CheckerBuilder().addChar("R").addInt32(TrueChecker()).addInt32(10)
    parser = ParserBuilder(UntilNullLists).addStringList("mechanisms")

class AuthenticationSASLContinue(MessageBase):
    checker = CheckerBuilder().addChar("R").addInt32(TrueChecker()).addInt32(11)
    parser = ParserBuilder().addByte("sasl_data")

class AuthenticationSASLFinal(MessageBase):
    checker = CheckerBuilder().addChar("R").addInt32(TrueChecker()).addInt32(12)
    parser = ParserBuilder().addByte("sasl_outcome")

class BackendKeyData(MessageBase):
    checker = CheckerBuilder().addChar("K").addInt32(TrueChecker())
    parser = ParserBuilder().addInt32("process_id").addByte("secret_key")

class BindComplete(MessageBase):
    checker = CheckerBuilder().addChar("2").addInt32(4)
    parser = ParserBuilder()

class CloseComplete(MessageBase):
    checker = CheckerBuilder().addChar("3").addInt32(4)
    parser = ParserBuilder()

class CommandComplete(MessageBase):
    checker = CheckerBuilder().addChar("C").addInt32(TrueChecker())
    parser = ParserBuilder().addString("command_tag")

class CopyInResponse(MessageBase):
    checker = CheckerBuilder().addChar("G").addInt32(TrueChecker())
    parser = ParserBuilder().addInt8("overall_format").addInt16("column_num").addInt16("column_formats", count=lambda ctx: ctx.decoded["column_num"][-1])

class CopyOutResponse(MessageBase):
    checker = CheckerBuilder().addChar("H").addInt32(TrueChecker())
    parser = ParserBuilder().addInt8("overall_format").addInt16("column_num").addInt16("column_formats", count=lambda ctx: ctx.decoded["column_num"][-1])

class CopyBothResponse(MessageBase):
    checker = CheckerBuilder().addChar("W").addInt32(TrueChecker())
    parser = ParserBuilder().addInt8("overall_format").addInt16("column_num").addInt16("column_formats", count=lambda ctx: ctx.decoded["column_num"][-1])

class DataRow(MessageBase):
    checker = CheckerBuilder().addChar("D").addInt32(TrueChecker())
    parser = ParserBuilder(CountLists).addInt16("num_column_values").addIntByteList("values", "num_column_values")

class EmptyQueryResponse(MessageBase):
    checker = CheckerBuilder().addChar("I").addInt32(4)
    parser = ParserBuilder()

class ErrorResponse(MessageBase):
    checker = CheckerBuilder().addChar("E").addInt32(TrueChecker())
    parser = ParserBuilder(UntilNullLists).addCharValuePairList("errors")

class FunctionCallResponse(MessageBase):
    checker = CheckerBuilder().addChar("V").addInt32(TrueChecker())
    parser = ParserBuilder(UntilNullLists).addInt32("len", unsigned=False).addByte("result_value", length=lambda ctx: ctx.decoded["len"][-1], condition=lambda ctx: ctx.decoded["len"][-1] != -1, default=None)

class NegotiateProtocolVersion(MessageBase):
    checker = CheckerBuilder().addChar("v").addInt32(TrueChecker())
    parser = ParserBuilder(CountLists).addInt32("minor_version").addInt32("num_unrecognized_options").addStringList("unrecognized_options", "num_unrecognized_options")

class NoData(MessageBase):
    checker = CheckerBuilder().addChar("n").addInt32(4)
    parser = ParserBuilder()

class NoticeResponse(MessageBase):
    checker = CheckerBuilder().addChar("N").addInt32(TrueChecker())
    parser = ParserBuilder(UntilNullLists).addCharValuePairList("notices")

class NotificationResponse(MessageBase):
    checker = CheckerBuilder().addChar("A").addInt32(TrueChecker())
    parser = ParserBuilder().addInt32("process_id").addString("channel").addString("payload")

class ParameterDescription(MessageBase):
    checker = CheckerBuilder().addChar("t").addInt32(TrueChecker())
    parser = ParserBuilder().addInt16("parameter_num").addInt32("object_ids", count=lambda ctx: ctx.decoded["parameter_num"][-1])

class ParameterStatus(MessageBase):
    checker = CheckerBuilder().addChar("S").addInt32(TrueChecker())
    parser = ParserBuilder().addString("run_time_param").addString("param_value")

class ParseComplete(MessageBase):
    checker = CheckerBuilder().addChar("1").addInt32(4)
    parser = ParserBuilder()

class PortalSuspended(MessageBase):
    checker = CheckerBuilder().addChar("s").addInt32(4)
    parser = ParserBuilder()

class ReadyForQuery(MessageBase):
    checker = CheckerBuilder().addChar("Z").addInt32(5)
    parser = ParserBuilder().addChar("transaction_status")

class RowDescription(MessageBase):
    checker = CheckerBuilder().addChar("T").addInt32(TrueChecker())
    parser = ParserBuilder().addInt16("field_num").addSequence(
        "fields", 
        ParserBuilder().addString("field_name")
                       .addInt32("table_OID")
                       .addInt16("column_attr")
                       .addInt32("type_OID")
                       .addInt16("type_size", unsigned=False)
                       .addInt32("type_modifier")
                       .addInt16("format_code"), 
        count=lambda ctx: ctx.decoded["field_num"][-1]
        )
