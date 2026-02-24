from typing import TypeAlias

from pyox.errors import SLR1ConflictError
from pyox.grammar import Grammar
from pyox.grammar import Production
from pyox.parser.lr.base import LRParser, ActionTable, GotoTable
from pyox.parser.lr.core import LR0Item, LR0ItemSet, lr0_closure

# type aliases
_StateList: TypeAlias = list[LR0ItemSet]
_StateIdMap: TypeAlias = dict[frozenset[LR0Item], int]


class SLR1Parser(LRParser):
    def __init__(self, grammar: Grammar, eof_symbol: str="$"):
        grammar.compute_first_sets()
        grammar.compute_follow_sets()
        self.grammar = grammar

        fake_start = LR0Item(Production(f"START{eof_symbol}", (grammar.start_symbol,)), 0)
        states, goto_table = self._build_states_and_goto_table(fake_start)
        action_table = self._build_action_table(eof_symbol, fake_start, states, goto_table)
        super().__init__(action_table, goto_table, eof_symbol)

    def _build_states_and_goto_table(self, fake_start: LR0Item) -> tuple[_StateList, GotoTable]:
        """
        Compute states and goto table or grammar.
        """
        i0 = lr0_closure(self.grammar, {fake_start})

        states: _StateList = [i0]
        state_ids: _StateIdMap = {frozenset(i0): 0}
        goto_table: GotoTable = {}

        i = 0
        while i < len(states):
            state = states[i]
            current_id = state_ids[frozenset(state)]
            goto_table[current_id] = {}

            possible_next_syms = {closure.production.rhs[closure.position] for closure in state if not closure.is_reducible()}

            for sym in possible_next_syms:
                items = {closure.move() for closure in state if not closure.is_reducible() and closure.production.rhs[closure.position] == sym}
                closure = lr0_closure(self.grammar, items)
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

    def _build_action_table(self, eof_symbol: str, fake_start: LR0Item, states: _StateList, goto_table: GotoTable) -> ActionTable:
        action_table: ActionTable = {
            i: {} for i in range(len(states))
        }

        conflicts = {i: set() for i in range(len(states))}

        for i, state in enumerate(states):
            for item in state:
                if not item.is_reducible():
                    sym = item.production.rhs[item.position]
                    if sym in self.grammar.terminals:
                        if sym in action_table[i]:
                            conflicts[i].add(sym)
                        action_table[i][sym] = ("shift",)

            for item in state:
                if item.is_reducible():
                    if item.production.lhs == fake_start.production.lhs:
                        if eof_symbol in action_table[i]:
                            conflicts[i].add(eof_symbol)
                        action_table[i][eof_symbol] = ("accept",)
                        continue

                    for a in self.grammar.follow_sets[item.production.lhs]:
                        if a in action_table[i]:
                            conflicts[i].add(a)
                        action_table[i][a] = (
                            "reduce",
                            item.production
                        )

        conflicts = [(states[i], ts) for i, ts in conflicts.items() if ts != set()]

        if len(conflicts) > 0:
            raise SLR1ConflictError(f"Conflicts in Action Table construction: {conflicts}")

        return action_table