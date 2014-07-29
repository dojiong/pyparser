from pyparser.tokenize import new_token_base
from pyparser.dfa import dfa_check


def test_simple():
    TokenBase = new_token_base()

    class Num(TokenBase):
        name = 'num'
        regular_expr = '[0-9]+'

    class String(TokenBase):
        name = 'str'
        regular_expr = "'(\\\\['rnt]|[^'])*'"

    dfa = TokenBase.generate_dfa()

    assert isinstance(dfa_check(dfa, "'asdf'"), String)
    assert isinstance(dfa_check(dfa, "'asdf\\'x'"), String)
    assert isinstance(dfa_check(dfa, "'asdf\\''"), String)
    assert isinstance(dfa_check(dfa, "'\\'asdf'"), String)
    assert isinstance(dfa_check(dfa, "'\\nasdf'"), String)
    assert dfa_check(dfa, "'\\asdf'") is None
    assert isinstance(dfa_check(dfa, "''"), String)
    assert isinstance(dfa_check(dfa, "1"), Num)
    assert isinstance(dfa_check(dfa, "1345"), Num)
    assert dfa_check(dfa, "'''") is None
    assert dfa_check(dfa, "'") is None
    assert dfa_check(dfa, "") is None
    assert dfa_check(dfa, "'as") is None
    assert dfa_check(dfa, "123#") is None
