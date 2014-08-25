

class NegLabel(object):
    __slots__ = ['labels']

    def __init__(self, labels):
        self.labels = set(labels)

    def __hash__(self):
        return id(self)

    def join(self, other):
        if not isinstance(other, NegLabel):
            raise Exception('invalid NegLabel')
        self.labels = self.labels.intersection(other.labels)

    def __eq__(self, other):
        return self.labels == other.labels


class DFAState(object):
    __slots__ = ['states', 'ids', 'arc_labels',
        'is_final', 'arcs', 'neg_label',
        'neg_state', 'data']

    def __init__(self):
        self.states = []
        self.arc_labels = set()
        self.arcs = {}
        self.is_final = False
        self.neg_label = None
        self.neg_state = None
        self.data = None
        self.ids = set()

    def next(self, label):
        state = self.arcs.get(label, None)
        if state is None:
            if self.neg_state is not None:
                if label not in self.neg_label.arcs:
                    state = self.neg_state
        return state

    def add(self, *nfas):
        for nfa in nfas:
            if nfa.id not in self.ids:
                self.states.append(nfa)
                self.ids.add(nfa.id)
                if nfa.is_final:
                    self.is_final = True
                    if self.data is not None and self.data is not nfa.data:
                        raise Exception('state accept the same data')
                    self.data = nfa.data
                for label, nfa_dsts in nfa.arcs.items():
                    if label is None:
                        continue
                    if isinstance(label, NegLabel):
                        if self.neg_label is not None:
                            self.neg_label.join(label)
                            self.neg_state.extend(nfa_dsts)
                            continue
                        self.neg_label = label
                        self.neg_state = nfa_dsts[:]
                        self.arcs[label] = self.neg_state
                    else:
                        nfas = self.arcs.get(label, None)
                        if nfas is None:
                            self.arcs[label] = nfa_dsts[:]
                        else:
                            nfas.extend(nfa_dsts)

    def out_equals(self, other):
        if self.is_final != other.is_final:
            return False
        if self.data is not other.data:
            return False
        if len(self.arcs) != len(other.arcs):
            return False
        for label, state in self.arcs.items():
            if state is not other.arcs.get(label, None):
                return False
        return True

    def replace(self, fr, to):
        if self.neg_state is fr:
            self.neg_state = to
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


def epsilon_closure(nfa, eps):
    eps.add(nfa)
    if None in nfa.arcs:
        for nfa_dst in nfa.arcs[None]:
            if nfa_dst not in eps:
                epsilon_closure(nfa_dst, eps)
    return eps


def epsilon_closure_set(nfas, boost, eps):
    ids = set()
    for nfa in nfas:
        cache = boost.get(nfa.id, None)
        if cache is None:
            cache = epsilon_closure(nfa, set())
            boost[nfa.id] = cache
        ids.update([x.id for x in cache])
        eps.update(cache)

    return '.'.join([str(x) for x in ids]), eps


def nfa2dfa(start_nfa):
    boost = {}
    start = DFAState()
    eps = epsilon_closure(start_nfa, set())
    boost[start_nfa.id] = eps
    start.add(*eps)
    ids = '.'.join([str(x) for x in start.ids])
    boost[ids] = start

    states = [start]
    for cur in states:
        arcs = {}
        for label, nfas in cur.arcs.items():
            ids, eps = epsilon_closure_set(nfas, boost, set())
            dfa = boost.get(ids, None)
            if dfa is None:
                dfa = DFAState()
                dfa.add(*eps)
                boost[ids] = dfa
                states.append(dfa)
            arcs[label] = dfa
        if cur.neg_label is not None:
            cur.neg_state = arcs[cur.neg_label]
        cur.arcs = arcs
    simplify_dfa(states)
    return start


def dfa_check(dfa, s):
    cur = dfa
    for c in s:
        next = cur.arcs.get(c, None)
        if next is None:
            if cur.neg_label is not None and c not in cur.neg_label.labels:
                cur = cur.neg_state
            else:
                return None
        else:
            cur = next
    if cur.is_final:
        return cur.data(s)
