from pyparser.tokenize import *
from pyparser.dfa import nfa2dfa


class FakeToken(object):

    def __init__(self, name, reg_expr):
        self.name = name
        self.regular_expr = reg_expr


def test_one_or_more():
    tok = TokenBuilder(FakeToken('abc', '[abc]+'))
    assert len(tok.root.arcs) == 3
    for c in 'abc':
        assert len(tok.root.arcs[c]) == 1
    tk = tok.root.arcs['a'][0]
    assert tk.is_final is True
    for c in 'abc':
        assert tok.root.arcs[c][0] is tk


def test_may_one():
    tok = TokenBuilder(FakeToken('abc', '[abc]?'))
    assert len(tok.root.arcs) == 4
    for c in ['a', 'b', 'c', None]:
        assert len(tok.root.arcs[c]) == 1
    tk = tok.root.arcs['a'][0]
    assert tk.is_final is True
    for c in ['a', 'b', 'c', None]:
        assert tok.root.arcs[c][0] is tk


def test_any():
    tok = TokenBuilder(FakeToken('abc', '[abc]*'))
    assert len(tok.root.arcs) == 4
    for c in ['a', 'b', 'c', None]:
        assert len(tok.root.arcs[c]) == 1
    tk = tok.root.arcs['a'][0]
    assert tk.is_final is True
    for c in ['a', 'b', 'c', None]:
        assert tok.root.arcs[c][0] is tk


def test_simple():
    tok = TokenBuilder(FakeToken('abc', 'abc'))
    assert len(tok.root.arcs) == 1
    assert len(tok.root.arcs['a']) == 1
    node1 = tok.root.arcs['a'][0]

    assert len(node1.arcs) == 1
    assert len(node1.arcs['b']) == 1
    node2 = node1.arcs['b'][0]

    assert len(node2.arcs) == 1
    assert len(node2.arcs['c']) == 1
    node3 = node2.arcs['c'][0]
    assert len(node3.arcs) == 0
    assert node3.is_final is True


def equal_state(a, b):
    if set(a.arcs.keys()) != set(b.arcs.keys()):
        return False
    for k, v in a.arcs.items():
        if len(v) != len(b.arcs[k]):
            return False
        for x, y in zip(v, b.arcs[k]):
            if not equal_state(x, y):
                return False
    return True


def test_eq():
    assert equal_state(TokenBuilder(FakeToken('abc', 'abc')).root,
                       TokenBuilder(FakeToken('abc', '(abc)')).root)


def test_dfa():
    tok = TokenBuilder(FakeToken('abc', '(ab)*ac'))
    s1 = nfa2dfa(tok.root)
    assert len(s1.arcs) == 1
    s2 = s1.arcs['a']
    assert len(s2.arcs) == 2
    assert s2.arcs['b'] is s1
    s3 = s2.arcs['c']
    assert len(s3.arcs) == 0
    assert s3.is_final is True
