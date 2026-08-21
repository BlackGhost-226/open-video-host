from . import Transitions
from .states import State
from .events import Event


transitions = Transitions()

transitions.addTransition(State.Startup, State.Idle, Event.StartupComplete)
transitions.addTransition(State.Idle, State.Query, Event.NewQuery)
transitions.addTransition(State.Query, State.Response, Event.EndOfQuery)
transitions.addTransition(State.Response, State.Idle, Event.ReadyForQuery)
