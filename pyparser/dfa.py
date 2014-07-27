

class DFAState(object):
    __slots__ = ['states', 'ids', 'arc_labels', 'is_final', 'freezed', 'arcs']

    def __init__(self):
        self.states = []
        self.ids = set()
        self.arc_labels = set()
        self.arcs = {}
        self.is_final = False
        self.freezed = False

    def __contains__(self, nfa):
        return nfa.id in self.ids

    def add(self, state):
        if self.freezed:
            raise Exception('state freezed')

        if state.id not in self.ids:
            self.states.append(state)
            self.ids.add(state.id)
            for label in state.arcs.keys():
                if label is not None:
                    self.arc_labels.add(label)
            if state.is_final:
                self.is_final = True

    def freeze(self):
        for label, state in self.get_arcs():
            self.arcs[label] = state
        self.ids = '.'.join([str(x) for x in self.ids])
        self.states = None
        self.freezed = True

    def get_arcs(self):
        for label in self.arc_labels:
            tstate = DFAState()
            for state in self.states:
                if label in state.arcs:
                    for s in state.arcs[label]:
                        s.epsilon_closure(tstate)
            yield label, tstate

    def out_equals(self, other):
        if len(self.arcs) != len(other.arcs):
            return False
        if self.is_final != other.is_final:
            return False
        for label, state in self.arcs.items():
            if state is not other.arcs.get(label, None):
                return False
        return True

    def replace(self, fr, to):
        for label, state in self.arcs.items():
            if state is fr:
                self.arcs[label] = to


def simplify_dfa(states):
    run = True
    while run:
        run = False
        for i, state in enumerate(states):
            for j in range(i + 1, len(states)):
                other_state = states[j]
                if state.out_equals(other_state):
                    del states[j]
                    for sub_state in states:
                        sub_state.replace(other_state, state)
                    run = True
                    break


def nfa2dfa(start):
    start = start.epsilon_closure()
    start.freeze()
    states = {start.ids: start}
    states_stack = [start]
    pending = [start]
    for cur in pending:
        for label, tstate in cur.arcs.items():
            tstate.freeze()
            old_tstate = states.get(tstate.ids, None)
            if old_tstate is None:
                states[tstate.ids] = tstate
                pending.append(tstate)
                states_stack.append(tstate)
            else:
                tstate = old_tstate
            cur.arcs[label] = tstate
    simplify_dfa(states_stack)
    return start
