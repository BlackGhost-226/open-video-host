import typing as t
from .errors import NotSupportedError, InternalError
from messages.simple.frontend import Query
from messages.simple.backend import RowDescription, DataRow, CommandComplete
from messages.readers import sync_read_simple_packet

from . import wait, adapt_params

from asyncio import IncompleteReadError

if t.TYPE_CHECKING:
    from .connection import Connection


class Cursor:
    def __init__(self, conn):
        self._rowDescSet = []
        self._dataRowsSet = []

        self._rowDescription: list[dict[str, t.Any]] = []
        self._dataRows: list[str] = []

        self.arraysize = 1

        self._conn: Connection = conn

    def close(self):
        del self

    @property
    def description(self) -> dict[dict[str, t.Any]]:
        if self._rowDescription == [] and self._rowDescSet != []:
            self.nextset()

        if self._rowDescription == []:
            return None

        rowDesc = []
        for colmun in self._rowDescription:
            rowDesc.append(self._build_column_description(colmun))
        return rowDesc
    
    def _build_column_description(self, col_data: dict) -> tuple:
        name = col_data["field_name"][0]
        type_code = col_data["type_OID"][0]
        internal_size = col_data["type_size"][0]
        #type_modifier = col_data["type_modifier"][0]

        precision = None
        scale = None

        display_size = None
        null_ok = None

        return (name, type_code, display_size, internal_size, precision, scale, null_ok)

    @property
    def rowcount(self) -> int:
        return len(self._dataRows) if self._dataRows is not None else -1

    def callproc(self, procname: str, *parameters):
        raise NotSupportedError("callproc() is not supported")

    def _execute(self, operation: str, *parameters):
        if not self._conn.transaction_began:
            self._conn.writer.write(Query.build({"query": ["BEGIN;"]}))
            self._conn.writer.flush()
            wait(self._conn.reader, "begining a transaction")
            self._conn.transaction_began = True

        self._conn.writer.write(Query.build({"query": [operation % tuple(adapt_params(parameters))]}))
        self._conn.writer.flush()

        self._dataRowsSet.append([])
        while True:
            try:
                packet = sync_read_simple_packet(self._conn.reader)
            except IncompleteReadError:
                raise InternalError("DataBase closed the connection")
            finally:
                if RowDescription.matches(packet):
                    self._rowDescSet.append(RowDescription.parse(packet)["fields"])
                elif DataRow.matches(packet):
                    self._dataRowsSet[-1].append(DataRow.parse(packet)["values"])
                elif CommandComplete.matches(packet):
                    break

    def execute(self, operation: str, *parameters):
        self._execute(operation, *parameters)
        wait(self._conn.reader, "executing a query")
        
    def executemany(self, operation: str, seq_of_parameters: tuple):
        for params in seq_of_parameters:
            self.execute(operation, params)
        wait(self._conn.reader, "executing querys")

    def fetchone(self):
        if self._dataRows == [] and self._dataRowsSet != []:
            self.nextset()
                    
        if self._dataRows == []:
            return None
        
        return self._dataRows.pop(0)

    def fetchmany(self, size: int = None):
        if size is None:
            size = self.arraysize

        fetchs = []
        for _ in range(size):
            fetchs.append(self.fetchone())
        return fetchs

    def fetchall(self):
        if self._dataRows == [] and self._dataRowsSet != []:
            self.nextset()
                    
        if self._dataRows == []:
            return None

        d = self._dataRows
        self._dataRows = []
        return d

    def nextset(self):
        self._rowDescription = self._rowDescSet.pop(0)
        self._dataRows = self._dataRowsSet.pop(0)

    def setinputsizes(self, sizes):
        pass

    def setoutputsize(self, size, *column):
        pass
