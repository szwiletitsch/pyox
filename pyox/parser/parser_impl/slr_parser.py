from collections import deque
from dataclasses import dataclass
from typing import TypeAlias, Iterator, Deque, Tuple

from pyox.datatypes import LexToken, ParseNode
from pyox.errors import SLR1ConflictError, ParseError
from pyox.grammar import Grammar
from pyox.parser import Parser


@dataclass(frozen=True)
class _ClosureItem:
    lhs: str
    rhs: tuple[str, ...]
    position: int

    def move(self):
        assert self.position < len(self.rhs)
        return _ClosureItem(self.lhs, self.rhs, self.position + 1)

    def is_reducible(self):
        return len(self.rhs) == self.position

    def __repr__(self):
        symbols = list(self.rhs)
        symbols.insert(self.position, ".")
        return f"{self.lhs} -> {' '.join(symbols)}"


# type aliases
_ClosureItemSet: TypeAlias = set[_ClosureItem]
_StateList: TypeAlias = list[_ClosureItemSet]
_StateIdMap: TypeAlias = dict[frozenset[_ClosureItem], int]
_GotoTable: TypeAlias = dict[int, dict[str, int]]
_ActionValue: TypeAlias = tuple[str] | tuple[str, str, tuple[str, ...]] | tuple[str, int]
_ActionTable: TypeAlias = dict[int, dict[str, _ActionValue]]


class SLR1Parser(Parser):
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.grammar.compute_first_sets()
        self.grammar.compute_follow_sets()

        self._eof_symbol = "$"
        self._fake_start = _ClosureItem(f"START{self._eof_symbol}", (self.grammar.start_symbol,), 0)
        self.states, self.goto_table = self._build_states_and_goto_table()
        self.action_table = self._build_action_table(self.states, self.goto_table)

    def _closure(self, items: _ClosureItemSet) -> _ClosureItemSet:
        """
        Compute closure of a set of LR(0) items.
        """
        considered_items: _ClosureItemSet = set()
        closure: _ClosureItemSet = set()
        closure.update(items)

        changed = True
        while changed:
            changed = False

            length_b4 = len(closure)

            # consider only new items
            for item in closure - considered_items:
                considered_items.add(item)

                if not item.is_reducible():
                    next_sym = item.rhs[item.position]
                    if next_sym in self.grammar.nonterminals:
                        for rhs in self.grammar.productions[next_sym]:
                            new_item = _ClosureItem(next_sym, tuple(rhs), 0)
                            closure.add(new_item)

            if length_b4 != len(closure):
                changed = True


        return closure

    def _build_states_and_goto_table(self) -> tuple[_StateList, _GotoTable]:
        """
        Compute states and goto table or grammar.
        """
        i0 = self._closure({self._fake_start})

        states: _StateList = [i0]
        state_ids: _StateIdMap = {frozenset(i0): 0}
        goto_table: _GotoTable = {}

        i = 0
        while i < len(states):
            state = states[i]
            current_id = state_ids[frozenset(state)]
            goto_table[current_id] = {}

            possible_next_syms = {closure.rhs[closure.position] for closure in state if not closure.is_reducible()}

            for sym in possible_next_syms:
                items = {closure.move() for closure in state if not closure.is_reducible() and closure.rhs[closure.position] == sym}
                closure = self._closure(items)
                frozen_closure = frozenset(closure)

                if frozen_closure not in state_ids:
                    state_id = len(states)
                    states.append(closure)
                    state_ids[frozen_closure] = state_id
                else:
                    state_id = state_ids[frozen_closure]

                goto_table[current_id][sym] = state_id

            i += 1

        return states, goto_table

    def _build_action_table(self, states: _StateList, goto_table: _GotoTable) -> _ActionTable:

        action_table: _ActionTable = {
            i: {} for i in range(len(states))
        }

        conflicts = {i: set() for i in range(len(states))}

        for i, state in enumerate(states):
            for item in state:
                if not item.is_reducible():
                    sym = item.rhs[item.position]
                    if sym in self.grammar.terminals:
                        if sym in action_table[i]:
                            conflicts[i].add(sym)
                        action_table[i][sym] = ("shift", goto_table[i][sym])

            for item in state:
                if item.is_reducible():
                    if item.lhs == self._fake_start.lhs:
                        if self._eof_symbol in action_table[i]:
                            conflicts[i].add(self._eof_symbol)
                        action_table[i][self._eof_symbol] = ("accept",)
                        continue

                    for a in self.grammar.follow_sets[item.lhs]:
                        if a in action_table[i]:
                            conflicts[i].add(a)
                        action_table[i][a] = (
                            "reduce",
                            item.lhs,
                            item.rhs
                        )

        conflicts = [(states[i], ts) for i, ts in conflicts.items() if ts != set()]

        if len(conflicts) > 0:
            raise SLR1ConflictError(f"Conflicts in Action Table construction: {conflicts}")

        return action_table

    def parse(self, tokens: Iterator[LexToken]) -> ParseNode:
        tokens = iter(list(tokens))
        eof_token = LexToken(
            type=self._eof_symbol,
            lexeme=self._eof_symbol,
            lineno=-1,
            colno=-1,
            start_index=-1,
            end_index=-1,
            value=-1,
        )
        token = next(tokens, eof_token)
        stack: Deque[Tuple[int, ParseNode | None]] = deque([(0, None)])

        while True:
            state_id, _ = stack[-1]
            action = self.action_table[state_id].get(token.type, ("error",))

            match action[0]:
                case "shift":
                    next_state = self.goto_table[state_id][token.type]

                    node = ParseNode(token.type)
                    node.token = token

                    stack.append((next_state, node))
                    token = next(tokens, eof_token) # skip

                case "reduce":
                    lhs, rhs = action[1:]
                    node = ParseNode(lhs)

                    children = []
                    for _ in range(len(rhs)):
                        _, child = stack.pop()
                        children.append(child)

                    # children were popped in reverse
                    node.children = list(reversed(children))

                    state_after_pop, _ = stack[-1]
                    next_state = self.goto_table[state_after_pop][lhs]

                    stack.append((next_state, node))
                    continue

                case "accept":
                    break

                case "error":
                    expected = [t for t, p in self.action_table[state_id].items() if p is not None]
                    raise ParseError(f"Unexpected token '{token.lexeme}' at position {token.lineno}:{token.colno}. Expected one of {expected}")

        root = stack[-1][1]
        return root


if __name__ == '__main__':
    def make_tokens(types):
        for i, t in enumerate(types):
            yield LexToken(type=t, lexeme="-", lineno=1, colno=i, start_index=-1, end_index=-1, value=-1)

    g = Grammar("E")
    g.add_production("E", ["E", "op", "T"])
    g.add_production("E", ["T"])
    g.add_production("T", ["(", "E", ")"])
    g.add_production("T", ["id"])

    SLR1Parser(g).parse(make_tokens(["(", "id", ")"])).pretty_print()


