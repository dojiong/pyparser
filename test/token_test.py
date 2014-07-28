from pyparser.tokenize import new_token_base
from pyparser.dfa import dfa_check
import pdb


def test_simple():
    TokenBase = new_token_base()

    class Num(TokenBase):
        name = 'num'
        regular_expr = '[0123456789]+'

    class String(TokenBase):
        name = 'str'
        regular_expr = '\'[^\']*\''

    dfa = TokenBase.generate_dfa()

    assert isinstance(dfa_check(dfa, "'asdf'"), String)
    assert isinstance(dfa_check(dfa, "''"), String)
    assert isinstance(dfa_check(dfa, "1"), Num)
    assert isinstance(dfa_check(dfa, "1345"), Num)
    assert dfa_check(dfa, "'''") is None
    assert dfa_check(dfa, "'") is None
    assert dfa_check(dfa, "") is None
