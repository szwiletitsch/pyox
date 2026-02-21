from typing import Iterator, Optional, List, Deque, Tuple
from collections import deque

from pyox.datatypes import LexToken, ParseNode
from pyox.errors import ParseError, LL1ConflictError
from pyox.grammar import Grammar
from pyox.parser import Parser


class LL1Parser(Parser):
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.grammar.compute_first_sets()
        self.grammar.compute_follow_sets()

        self._eof_symbol = "$"
        self._top_down_table = self._build_top_down_table()

    def _build_top_down_table(self):
        value: Optional[List[str]] = None
        table = {n: {t: value for t in self.grammar.terminals | {self._eof_symbol}} for n in self.grammar.nonterminals}

        conflicts = {n: set() for n in self.grammar.nonterminals}

        for lhs, productions in self.grammar.productions.items():
            for rhs in productions:

                nullable = True
                for symbol in rhs:
                    for first in self.grammar.first_sets[symbol] - {"ε"}:
                        if table[lhs][first] is not None:
                            conflicts[lhs].add(first)
                        table[lhs][first] = rhs
                    if "ε" not in self.grammar.first_sets[symbol]:
                        nullable = False
                        break

                if nullable:
                    for follow in self.grammar.follow_sets[lhs]:
                        if table[lhs][follow] is not None:
                            conflicts[lhs].add(follow)
                        table[lhs][follow] = rhs

        conflicts = [(n, ts) for n, ts in conflicts.items() if ts != set()]
        if len(conflicts) > 0:
            raise LL1ConflictError(f"Conflicts in Parse Table construction: {conflicts}")

        return table

    def parse(self, tokens: Iterator[LexToken]) -> ParseNode:
        tokens = iter(list(tokens))
        token = next(tokens, None)

        root = ParseNode(self.grammar.start_symbol)
        stack: Deque[Tuple[str, ParseNode]] = deque([(self._eof_symbol, None), (self.grammar.start_symbol, root)])

        while stack:
            stack_sym, node = stack.pop()

            if stack_sym in self.grammar.nonterminals:
                if token is None and self._top_down_table[stack_sym].get(self._eof_symbol) is None:
                    raise ParseError("Unexpected EOF")

                rhs = self._top_down_table[stack_sym].get(token.type) if token else []
                if rhs is None:
                    expected = [t for t, p in self._top_down_table[stack_sym].items() if p is not None]
                    raise ParseError(f"Unexpected token '{token.lexeme}' at position {token.lineno}:{token.colno}. Expected one of {expected}")

                children_nodes = [ParseNode(sym) for sym in rhs]
                node.children = children_nodes

                for sym_node in reversed(list(zip(rhs, children_nodes))):
                    stack.append(sym_node)

            elif stack_sym in self.grammar.terminals:
                if token is None or stack_sym != token.type:
                    raise ParseError(f"Unexpected token '{token.lexeme if token else 'EOF'}' at position {token.lineno}:{token.colno}. Expected '{stack_sym}'")

                node.token = token
                token = next(tokens, None) # skip token

            elif stack_sym == self._eof_symbol:
                if token is not None:
                    raise ParseError(f"Extra token after parsing: '{token.lexeme}' at position {token.lineno}:{token.colno}.")
                break

        return root