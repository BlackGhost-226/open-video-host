from json_lang import Lib
from .. import GWClient

sql_lib = Lib("sql")

@sql_lib.add_func
def add(table: str, **kwargs):
    return GWClient.add_row_to_db(table=table, **kwargs)[0]

@sql_lib.add_func
def get(table: str, **kwargs):
    return GWClient.get_row_from_db(table=table, **kwargs)[0]

#@sql_lib.add_func
def edit():
    pass
