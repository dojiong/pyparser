from .tokenize import new_token_base
from .dfa import NFAState, nfa2dfa


ASTTokenBase = new_token_base()


class Num(ASTTokenBase):
    regular_expr = '[0-9]+'


class String(ASTTokenBase):
    __slots__ = ['string']
    regular_expr = "'[^']*'"

    def __init__(self, data):
        # TODO string escape
        self.data = data[1:-1]

    def __hash__(self):
        return hash(self.data)

    def __eq__(self, other):
        return self.data == other.data


class Name(ASTTokenBase):
    regular_expr = '[a-zA-Z_][a-zA-Z_0-9]*'


class LeftOp(ASTTokenBase):
    regular_expr = '\\('


class RightOp(ASTTokenBase):
    regular_expr = '\\)[?+*]?'


class Eq(ASTTokenBase):
    regular_expr = '='


class Or(ASTTokenBase):
    regular_expr = '\\|'


class EndRule(ASTTokenBase):
    regular_expr = ';'


class Blank(ASTTokenBase):
    regular_expr = '[ \t\r\n]+'
    ignore = True


class Comment(ASTTokenBase):
    regular_expr = '#[^\n]*'
    ignore = True


ast_tokenizer = ASTTokenBase.get_tokenizer()


class TokenLabel(object):
    __slots__ = ['token', 'cmp_tk']

    def __init__(self, token, cmp_tk=False):
        self.token = token
        self.cmp_tk = cmp_tk

    def __hash__(self):
        if self.cmp_tk:
            return hash(self.token)
        return hash(self.token.__class__)

    def __eq__(self, obj):
        if self.cmp_tk:
            return self.token == obj
        return isinstance(obj, self.__class__)


class GrammarError(Exception):
    pass


class GrammarRule(object):
    pass


class ASTBuilder(object):

    def __init__(self, token_base, grammar):
        self.token_base = token_base
        self.tokenizer = token_base.get_tokenizer()
        self.grammar = grammar
        self._build_rules()

    def _preprocess_rules(self):
        tks = ast_tokenizer.tokens(self.grammar)

        def next_tk(tp=None):
            try:
                tk = next(tks)
                if tp is not None and not isinstance(tk, tp):
                    raise GrammarError('except %s, got %r' % (tp.__name__, tk))
                return tk
            except StopIteration:
                pass
        rules = {}
        while True:
            name = next_tk(Name)
            if name is None:
                break
            if name.data in rules:
                raise GrammarError('duplicated rule %s' % name.data)
            elif self.tokenizer.get_token_cls(name.data) is not None:
                raise GrammarError('duplicated with token %s' % name.data)

            next_tk(Eq)
            rule_tks = []
            while True:
                tk = next_tk()
                if tk is None:
                    raise GrammarError('missing `;` at end')
                if isinstance(tk, EndRule):
                    break
                rule_tks.append(tk)
            rules[name.data] = (type(name.data, (GrammarRule,), {}), rule_tks)
        return rules

    def _build_rules(self):
        rules = {}
        pre_rules = self._preprocess_rules()
        for rule_name, (rulecls, tks) in pre_rules.items():
            par_stack = []
            cur = root = NFAState()
            for tk in tks:
                if cur is None:
                    raise GrammarError('invalid token: %r' % tk)
                if isinstance(tk, LeftOp):
                    par_stack.append([cur, None])
                elif isinstance(tk, RightOp):
                    if len(par_stack) == 0:
                        raise GrammarError('invalid `)`, missing `(`')
                    start, end = par_stack.pop()
                    if end is None:
                        end = cur
                    if start is end:
                        raise GrammarError('empty `()`')
                    if len(tk.data) == 2:
                        op = tk.data[1]
                        if op == '?':
                            start.arc(None, end)
                        elif op == '+':
                            end.arc(None, start)
                        elif op == '*':
                            start.arc(None, end)
                            end.arc(None, start)
                        if cur is not end:
                            cur = cur.arc(None, end)
                elif isinstance(tk, Or):
                    if len(par_stack) == 0:
                        raise GrammarError('invalid `|`, missing `(`')
                    start, end = par_stack[-1]
                    if end is None:
                        par_stack[-1][1] = cur
                    if start is cur:
                        raise GrammarError('invalid `(|`')
                    cur = start
                elif isinstance(tk, Name):
                    label = self.tokenizer.get_token_cls(tk.data)
                    if label is None:
                        label, _ = pre_rules.get(tk.data, None)
                        if label is None:
                            raise GrammarError('unknown %s' % tk.data)
                    cur = cur.arc(label, NFAState())
                elif isinstance(tk, String):
                    cur = cur.arc(tk.data, NFAState())
            cur.is_final = True
            cur.data = rulecls
            rulecls.root = nfa2dfa(root)
            rules[rule_name] = rulecls
        self.rules = rules

    def build(self, src):
        pass
