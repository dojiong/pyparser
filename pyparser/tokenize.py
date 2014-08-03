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
                start, or_end = par_stack.pop()
                if or_end is not None:
                    cur = cur.arc(None, or_end)
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
                    elif char == '-':
                        if i + 1 == len(self.reg_expr) or len(chars) == 0:
                            raise Exception('invalid range -')
                        end_char = self.reg_expr[i + 1]
                        start_char = chars[-1]
                        if start_char >= end_char:
                            raise Exception('invalid range')
                        chars.extend(
                            [chr(x) for x in range(
                                ord(start_char) + 1, ord(end_char) + 1)])
                        i += 2
                        continue
                    elif char == '\\':
                        if i + 1 == len(self.reg_expr):
                            raise Exception('invalid escape')
                        next_char = self.reg_expr[i + 1]
                        if next_char in ']\\-':
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


class Tokenizer(object):
    def __init__(self, token_base, root):
        self.token_base = token_base
        self.root = root

    def tokens(self, data):
        cur = self.root
        start_i = 0
        i = 0
        lineno = 1
        line_index = 0
        while i < len(data):
            char = data[i]
            next = cur.next(char)
            if next is None:
                if cur.is_final:
                    if not cur.data.ignore:
                        yield cur.data(data[start_i:i])
                    start_i = i
                    cur = self.root
                else:
                    raise self.token_base.UnexpectedCharError(
                        lineno, line_index, char)
            else:
                cur = next
                i += 1
                line_index += 1
                if char == '\n':
                    lineno += 1
                    line_index = 0
        if cur.is_final:
            if not cur.data.ignore:
                yield cur.data(data[start_i:])
        else:
            raise self.token_base.UnexpectedEOFError()


class TokenBaseMixin(object):

    def __init__(self, data):
        self.data = data

    @classmethod
    def generate_dfa(cls):
        states = cls.__token_states__
        root = TokenState()
        for state in states.values():
            root.arc(None, state)
        dfa = nfa2dfa(root)
        if dfa.is_final:
            raise Exception(
                'invalid token, accept empty string: %s' % dfa.data.name)
        return dfa

    @classmethod
    def get_tokenizer(cls):
        return Tokenizer(cls, cls.generate_dfa())

    def __repr__(self):
        return '%s(%r)' % (self.__class__.__name__, self.data)

    def __eq__(self, other):
        return other.__class__ == self.__class__ and other.data == self.data


def new_token_base():
    class TokenMeta(type):
        def __new__(meta, name, bases, attrs):
            if '__token_base__' in attrs:
                attrs.pop('__token_base__')
                return type.__new__(meta, name, bases, attrs)

            reg_expr = attrs.get('regular_expr', None)
            if reg_expr is None:
                raise TypeError('missing regular_expr')
            if 'ignore' not in attrs:
                attrs['ignore'] = False

            cls = type.__new__(meta, name, bases, attrs)
            states = cls.__token_states__
            if name in states:
                raise TypeError('Token %s duplicated' % name)
            states[name] = TokenBuilder(cls).root
            return cls

    class UnexpectedCharError(Exception):
        def __init__(self, lineno, index, char):
            self.lineno = lineno
            self.index = index
            self.char = char

        def __str__(self):
            return 'unexpected char at line %d:%d %r' % (
                self.lineno, self.index, self.char)

    class UnexpectedEOFError(Exception):
        pass

    return TokenMeta('TokenBase', (TokenBaseMixin,),
        {'__token_states__': {},
         '__token_base__': True,
         'UnexpectedCharError': UnexpectedCharError,
         'UnexpectedEOFError': UnexpectedEOFError})
