class Transitions:
    def __init__(self):
        self.transitions: dict[int, dict[int, int]] = {}

    def addTransition(self, from_state: int, to_state: int, on_event: int):
        if self.transitions.get(from_state) == None:
            self.transitions[from_state] = {}
        self.transitions[from_state][on_event] = to_state

    def getNewState(self, current_state: int, event: int):
        return self.transitions.get(current_state, {}).get(event)

class StateMachine:
    def __init__(self, initial_state: int, transitions: Transitions):
        self.state: int = initial_state
        self.transits: Transitions = transitions

    def transition(self, event: int) -> bool: # Use Enums
        state = self.transits.getNewState(self.state, event)
        if state != None:
            self.state = state
            return True
        return False

if __name__ == "__main__":
    from enum import Enum

    class State(Enum):
        S1 = 1
        S2 = 2
        S3 = 3

    class Event(Enum):
        S1ToS2 = 1
        S2ToS3 = 2
        S3ToS1 = 3

    trs = Transitions()
    trs.addTransition(State.S1, State.S2, Event.S1ToS2)
    trs.addTransition(State.S2, State.S3, Event.S2ToS3)
    trs.addTransition(State.S3, State.S1, Event.S3ToS1)

    machine = StateMachine(State.S1, trs)

    print(machine.state) # S1

    machine.transition(Event.S1ToS2)
    print(machine.state) # S2

    machine.transition(Event.S2ToS3)
    print(machine.state) # S3

    machine.transition(Event.S3ToS1)
    print(machine.state) # S1

    machine.transition(Event.S3ToS1)
    print(machine.state) # S1
