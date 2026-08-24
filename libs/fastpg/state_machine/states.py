from enum import Enum

class State(Enum):
    Startup = 1
    Idle = 2

    ExtendedQuery = 3
    SimpleQuery = 4

    QueryResponse = 5

    Unknow = 6
