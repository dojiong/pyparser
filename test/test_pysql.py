from pyparser.tokenize import new_token_base
from pyparser.ast import ASTBuilder


TokenBase = new_token_base()


class Name(TokenBase):
    regular_expr = '[a-zA-Z_][a-zA-Z_0-9]*'


class PyCode(TokenBase):
    regular_expr = '({[^}]+}|.+)'


class SQLCode(TokenBase):
    regular_expr = '[^{]+'


class Comment(TokenBase):
    regular_expr = '#[^\n]*(\n)?'
    ignore = True


class Blank(TokenBase):
    regular_expr = '[ \t\r\n]+'
    ignore = True


def test_tokens():
    data = open('test_grammar').read()
    ast = ASTBuilder(TokenBase, data)
    ast.build('uid->getuser(uid) select * from table')


if __name__ == '__main__':
    test_tokens()
