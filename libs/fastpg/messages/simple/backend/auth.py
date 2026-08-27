from ... import CheckerBuilder, ParserBuilder, MessageBase
from ...checkers import Lenght
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
    checker = CheckerBuilder().addChar("R").addInt32(Lenght()).addInt32(8)
    parser = ParserBuilder().addByte("auth_data")

class AuthenticationSSPI(MessageBase):
    checker = CheckerBuilder().addChar("R").addInt32(8).addInt32(9)
    parser = ParserBuilder()

class AuthenticationSASL(MessageBase):
    checker = CheckerBuilder().addChar("R").addInt32(Lenght()).addInt32(10)
    parser = ParserBuilder(UntilNullLists).addStringList("mechanisms")

class AuthenticationSASLContinue(MessageBase):
    checker = CheckerBuilder().addChar("R").addInt32(Lenght()).addInt32(11)
    parser = ParserBuilder().addByte("sasl_data")

class AuthenticationSASLFinal(MessageBase):
    checker = CheckerBuilder().addChar("R").addInt32(Lenght()).addInt32(12)
    parser = ParserBuilder().addByte("sasl_outcome")

class NegotiateProtocolVersion(MessageBase):
    checker = CheckerBuilder().addChar("v").addInt32(Lenght())
    parser = ParserBuilder(CountLists).addInt32("minor_version").addInt32("num_unrecognized_options").addStringList("unrecognized_options", "num_unrecognized_options")
