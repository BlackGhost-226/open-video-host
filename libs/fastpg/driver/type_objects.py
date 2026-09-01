# https://peps.python.org/pep-0249/#type-objects-and-constructors

array_map = {}

class DBAPITypeObject:
    def __init__(self, *values):
        self.values = set(values)

    def __eq__(self, other):
        if isinstance(other, DBAPITypeObject):
            return bool(self.values & other.values)
        return other in self.values

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return f"<DBAPITypeObject {self.values}>"

def is_array(oid: int) -> bool:
    """Returns True if the given OID is a recognized array OID."""
    return oid in array_map

def get_base_oid(array_oid: int) -> int:
    """Returns the base element OID for an array OID, or the OID itself if it's already a scalar."""
    return array_map.get(array_oid, array_oid)

def populate_array_map(conn):
    cur = conn.cursor()

    cur.execute("SELECT oid, typelem FROM pg_type WHERE typelem != 0") # typelem != 0 selects only array types
    for array_oid, base_element_oid in cur.fetchall():
        array_oid = int(array_oid.decode("ascii"))
        base_element_oid = int(base_element_oid.decode("ascii"))
        array_map[array_oid] = base_element_oid

    conn.commit()
    cur.close()

# --- PEP 249 Standard Types ---
STRING = DBAPITypeObject(18, 19, 24, 25, 194, 3361, 3402, 5017, 5069, 1033, 1042, 1043, 3220, 4072, 2970, 5038) # 1033 3220 jsonpath:4072 2970 5038
BINARY = DBAPITypeObject(17, 1560, 1562)
NUMBER = DBAPITypeObject(20, 21, 22, 23, 28, 29, 30, 700, 701, 1700, 3904, 3906, 3926, 4451, 4532, 4536) # 22
DATETIME = DBAPITypeObject(1082, 1083, 1114, 1184, 1186, 1266, 3908, 3910, 3912, 4533, 4534, 4535)
ROWID = DBAPITypeObject(26, 27)

# --- Driver Specific Extensions ---
# https://github.com/postgres/postgres/blob/master/src/include/catalog/pg_type.dat
BOOL = DBAPITypeObject(16)
JSON = DBAPITypeObject(114, 3802)
XML = DBAPITypeObject(142)
GEO = DBAPITypeObject(600, 601, 602, 603, 604, 628, 718)
MONEY = DBAPITypeObject(790)
NETWORK = DBAPITypeObject(829, 869, 650, 774)
UUID = DBAPITypeObject(2950)

PSEUDO_TYPE = DBAPITypeObject(705, 2249, 2287, 2275, 2276, 2277, 2278, 2279, 3838, 2280, 2281, 2283, 2776, 3500, 3115, 325, 3310, 269, 3831, 5077, 5078, 5079, 5080, 4537, 4538, 4600, 4601, 6437)
TEXT_SEARCH = DBAPITypeObject(3614, 3642, 3615, 3734, 3769)
REG = DBAPITypeObject(1790, 2202, 2203, 2204, 2205, 4191, 2206, 4096, 4089, 6490)
ROWTYPE = DBAPITypeObject(71, 75, 81, 83)

if __name__ == "__main__":
    print(1042 == STRING)
    print(STRING == 1042)
    print(STRING == STRING)
