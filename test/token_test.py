from pyparser.tokenize import new_token_base
from pyparser.dfa import dfa_check


def test_simple():
    TokenBase = new_token_base()

    class Num(TokenBase):
        regular_expr = '[0-9]+'

    class String(TokenBase):
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


struct_a = '''struct user {
    name: string
    id: int64
    email: string
}
'''


def test_tokens():
    TokenBase = new_token_base()

    class Num(TokenBase):
        regular_expr = '[0-9]+'

    class String(TokenBase):
        regular_expr = "'(\\\\['rnt]|[^'])*'"

    class Name(TokenBase):
        regular_expr = '[a-zA-Z_][a-zA-Z_0-9]*'

    class Op(TokenBase):
        regular_expr = '[{}()[\\]+\\-*/:]'

    class Newline(TokenBase):
        regular_expr = '((\r)?\n)((\r)?\n| )*'

    class Blank(TokenBase):
        regular_expr = '[ \t]+'
        ignore = True

    tks = [
        Name('struct'), Name('user'), Op('{'), Newline('\n    '),
            Name('name'), Op(':'), Name('string'), Newline('\n    '),
            Name('id'), Op(':'), Name('int64'), Newline('\n    '),
            Name('email'), Op(':'), Name('string'), Newline('\n'),
        Op('}'), Newline('\n'),
    ]

    tokenize = TokenBase.get_tokenizer()
    for token, expect in zip(tokenize.tokens(struct_a), tks):
        assert token == expect
