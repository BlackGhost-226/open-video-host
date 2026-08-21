from enum import Enum

class Event(Enum):
    StartupComplete = 1
    NewQuery = 2
    EndOfQuery = 3
    ReadyForQuery = 4