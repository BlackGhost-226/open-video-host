from .... import CheckerBuilder, ParserBuilder, MessageBase
from ....checkers import TrueChecker
from ....extensions import CountLists


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
    
class DataRow(MessageBase):
    checker = CheckerBuilder().addChar("D").addInt32(TrueChecker())
    parser = ParserBuilder(CountLists).addInt16("num_column_values").addIntByteList("values", "num_column_values")

class EmptyQueryResponse(MessageBase):
    checker = CheckerBuilder().addChar("I").addInt32(4)
    parser = ParserBuilder()
