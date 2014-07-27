from collections import defaultdict
from .dfa import DFAState


class TokenState(object):
    __slots__ = ['arcs', 'is_final', 'id']
    _auto_id = 0

    def __init__(self):
        self.arcs = defaultdict(lambda: [])
        self.is_final = False
        self.id = self.get_id()

    @classmethod
    def get_id(cls):
        cls._auto_id += 1
        return cls._auto_id - 1

    def epsilon_closure(self, tstate=None):
        ret = tstate or DFAState()
        ret.add(self)
        if None in self.arcs:
            for state in self.arcs[None]:
                if state not in ret:
                    state.epsilon_closure(ret)
        return ret

    def arc(self, char, node):
        assert node is not None
        self.arcs[char].append(node)
        return node

    def copy_from(self, start, end):
        ret = None
        for char, nodes in start.arcs.items():
            for node in nodes:
                new_node = self.arc(char, TokenState())
                if node is end:
                    ret = new_node
                else:
                    new_node.copy_from(node, end)
        return ret

    def __eq__(self, node):
        if set(self.arcs.keys()) != set(node.arcs.keys()):
            return False
        for k, v in self.arcs.items():
            if v != node.arcs[k]:
                return False
        return True


class Token(object):
    def __init__(self, name, reg_expr):
        self.name = name
        self.reg_expr = reg_expr
        self.make_states()

    def make_states(self):
        par_stack = [] # for ()
        in_bra_stack = [] # for ()/[] pair check
        root = TokenState()
        cur = root
        i = 0
        while i < len(self.reg_expr):
            char = self.reg_expr[i]
            if char == '(':
                par_stack.append(cur)
                in_bra_stack.append(None)
            elif char == ')':
                if len(in_bra_stack) == 0 or in_bra_stack[-1]:
                    raise Exception('unmatched `()`')
                i += 1
                start = par_stack.pop()
                if i < len(self.reg_expr):
                    next_char = self.reg_expr[i]
                    if next_char == '?':
                        self.sub_may_one(start, cur)
                    elif next_char == '+':
                        self.sub_one_or_more(start, cur)
                    elif next_char == '*':
                        self.sub_any(start, cur)
                in_bra_stack.pop()
            elif char == '[':
                in_bra_stack.append(TokenState())
            elif char == ']':
                if len(in_bra_stack) == 0 or not in_bra_stack[-1]:
                    raise Exception('unmatched `[]`')
                i += 1
                end = in_bra_stack.pop()
                if i < len(self.reg_expr):
                    next_char = self.reg_expr[i]
                    if next_char == '?':
                        self.sub_may_one(cur, end)
                        cur = end
                    elif next_char == '+':
                        self.sub_one_or_more(cur, end)
                        cur = end
                    elif next_char == '*':
                        self.sub_any(cur, end)
                        cur = end
            elif char == '\\':
                # \\,\?,\+,\*,\[
                i += 1
                if i == len(self.reg_expr):
                    raise Exception('invalid escape(at end)')
                next_char = self.reg_expr[i]
                if next_char in '\\?+*()[]':
                    if len(in_bra_stack) and in_bra_stack[-1]:
                        cur.arc(next_char, in_bra_stack[-1])
                    else:
                        cur = cur.arc(next_char, TokenState())
                else:
                    raise Exception('invalid escape')
            else:
                if len(in_bra_stack) and in_bra_stack[-1]:
                    cur.arc(char, in_bra_stack[-1])
                else:
                    cur = cur.arc(char, TokenState())
            i += 1
        cur.is_final = True
        self.root = root

    def sub_any(self, start, cur):
        # (xx)*
        start.arc(None, cur)
        cur.arc(None, start)

    def sub_may_one(self, start, cur):
        # (xx)?
        start.arc(None, cur)

    def sub_one_or_more(self, start, cur):
        # (xx)+
        new_end = cur.copy_from(start, cur)
        new_end.arc(None, cur)

    def parse(self, stream):
        pass


class Tokens(object):
    def __init__(self):
        self.tokens = []

    def add(self, tok):
        self.tokens.append(tok)
