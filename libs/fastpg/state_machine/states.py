from enum import Enum

class State(Enum):
    Startup = 1
    Query = 2
    Response = 3
    Idle = 4
