from collections import defaultdict
from .dfa import DFAState, nfa2dfa, NegLabel


class TokenState(object):
    __slots__ = ['arcs', 'is_final', 'id', 'data', 'accept_any']
    _auto_id = 0

    def __init__(self):
        self.arcs = defaultdict(lambda: [])
        self.is_final = False
        self.data = None
        self.accept_any = False
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

    def __eq__(self, node):
        # for test compare
        if set(self.arcs.keys()) != set(node.arcs.keys()):
            return False
        for k, v in self.arcs.items():
            if v != node.arcs[k]:
                return False
        return True


class TokenBuilder(object):

    def __init__(self, cls):
        self.token = cls
        self.reg_expr = cls.regular_expr
        self.make_states()

    def make_states(self):
        # FIXME code tidy
        par_stack = []  # for ()
        root = TokenState()
        cur = root
        i = 0
        while i < len(self.reg_expr):
            char = self.reg_expr[i]
            if char == '(':
                par_stack.append([cur, None])
            elif char == ')':
                start, or_state = par_stack.pop()
                if or_state is not None:
                    cur = or_state
                i += 1
                if i < len(self.reg_expr):
                    next_char = self.reg_expr[i]
                    if next_char == '?':
                        self.sub_may_one(start, cur)
                    elif next_char == '+':
                        self.sub_one_or_more(start, cur)
                    elif next_char == '*':
                        self.sub_any(start, cur)
                    else:
                        i -= 1
            elif char == '|':
                if len(par_stack) == 0:
                    raise Exception('invalid `|`,not in ()')
                start = par_stack[-1]
                if start[1] is None:
                    start[1] = TokenState()
                cur.arc(None, start[1])
                cur = start[0]
            elif char == '[':
                neg = False
                i += 1
                if i < len(self.reg_expr):
                    next_char = self.reg_expr[i]
                    if next_char == '^':
                        neg = True
                        i += 1
                pair_made = False
                chars = []
                while i < len(self.reg_expr):
                    char = self.reg_expr[i]
                    if char == ']':
                        pair_made = True
                        break
                    elif char == '\\':
                        if i + 1 == len(self.reg_expr):
                            raise Exception('invalid escape')
                        next_char = self.reg_expr[i + 1]
                        if next_char in ']\\':
                            char = next_char
                        else:
                            raise Exception('invalid escape')
                        i += 1
                    chars.append(char)
                    i += 1
                if not pair_made:
                    raise Exception('unmatched []')
                end = TokenState()
                if neg:
                    cur.arc(NegLabel(chars), end)
                else:
                    for char in chars:
                        cur.arc(char, end)
                i += 1
                if i < len(self.reg_expr):
                    next_char = self.reg_expr[i]
                    if next_char == '?':
                        self.sub_may_one(cur, end)
                    elif next_char == '+':
                        self.sub_one_or_more(cur, end)
                    elif next_char == '*':
                        self.sub_any(cur, end)
                    else:
                        i -= 1
                cur = end
            elif char == '\\':
                # \\,\?,\+,\*,\[
                i += 1
                if i == len(self.reg_expr):
                    raise Exception('invalid escape(at end)')
                next_char = self.reg_expr[i]
                if next_char in '\\?+*()[|':
                    cur = cur.arc(next_char, TokenState())
                else:
                    raise Exception('invalid escape')
            else:
                cur = cur.arc(char, TokenState())
            i += 1
        if len(par_stack) != 0:
            raise Exception('unmatched ()')
        cur.is_final = True
        cur.data = self.token
        self.root = root
        return root

    def sub_any(self, start, end):
        # (xx)*
        start.arc(None, end)
        end.arc(None, start)

    def sub_may_one(self, start, end):
        # (xx)?
        start.arc(None, end)

    def sub_one_or_more(self, start, end):
        # (xx)+
        end.arc(None, start)


class TokenBaseMixin(object):

    def __init__(self, data):
        self.data = data

    @classmethod
    def generate_dfa(cls):
        states = cls.__token_states__
        root = TokenState()
        for state in states.values():
            root.arc(None, state)
        cls.dfa = nfa2dfa(root)
        return cls.dfa


def new_token_base():
    class TokenMeta(type):
        def __new__(meta, name, bases, attrs):
            if '__token_base__' in attrs:
                attrs.pop('__token_base__')
                return type.__new__(meta, name, bases, attrs)

            name = attrs.get('name', None)
            reg_expr = attrs.get('regular_expr', None)
            if name is None or reg_expr is None:
                raise TypeError('missing name or regular_expr')

            cls = type.__new__(meta, name, bases, attrs)
            states = cls.__token_states__
            if name in states:
                raise TypeError('Token %s duplicated' % name)
            states[name] = TokenBuilder(cls).root
            return cls

    return TokenMeta('TokenBase', (TokenBaseMixin,),
        {'__token_states__': {}, '__token_base__': True})
