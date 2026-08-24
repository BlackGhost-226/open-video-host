from enum import Enum

class Event(Enum):
    StartupComplete = 1

    NewExtendedQuery = 2
    NewSimpleQuery = 3

    EndOfQuery = 4
    ReadyForQuery = 5

    UnknowPacket = 6