from . import Transitions
from .states import State
from .events import Event


transitions = Transitions()

transitions.addTransition(State.Startup, State.Idle, Event.StartupComplete)
transitions.addTransition(State.Idle, State.Unknow, Event.UnknowPacket)


transitions.addTransition(State.Idle, State.ExtendedQuery, Event.NewExtendedQuery)
transitions.addTransition(State.Idle, State.SimpleQuery, Event.NewSimpleQuery)

transitions.addTransition(State.ExtendedQuery, State.QueryResponse, Event.EndOfQuery)
transitions.addTransition(State.SimpleQuery, State.QueryResponse, Event.EndOfQuery)

transitions.addTransition(State.Unknow, State.Idle, Event.ReadyForQuery)
transitions.addTransition(State.QueryResponse, State.Idle, Event.ReadyForQuery)
