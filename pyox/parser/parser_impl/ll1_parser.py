from typing import Iterator, Optional, List, Deque, Tuple
from collections import deque

from pyox.datatypes import LexToken, ParseNode
from pyox.errors import ParseError, LL1ConflictError
from pyox.grammar import Grammar, Production
from pyox.parser import Parser


class LL1Parser(Parser):
    def __init__(self, grammar: Grammar):
        self.grammar = grammar
        self.grammar.compute_first_sets()
        self.grammar.compute_follow_sets()

        self._eof_symbol = "$"
        self._top_down_table = self._build_top_down_table()

    def _build_top_down_table(self):
        value: Optional[Production] = None
        table = {n: {t: value for t in self.grammar.terminals | {self._eof_symbol}} for n in self.grammar.nonterminals}

        conflicts = {n: set() for n in self.grammar.nonterminals}

        for production in self.grammar.productions:
            lhs, rhs = production.lhs, production.rhs

            nullable = True
            for symbol in rhs:
                for first in self.grammar.first_sets[symbol] - {"ε"}:
                    if table[lhs][first] is not None:
                        conflicts[lhs].add(first)
                    table[lhs][first] = production
                if "ε" not in self.grammar.first_sets[symbol]:
                    nullable = False
                    break

            if nullable:
                for follow in self.grammar.follow_sets[lhs]:
                    if table[lhs][follow] is not None:
                        conflicts[lhs].add(follow)
                    table[lhs][follow] = production

        conflicts = [(n, ts) for n, ts in conflicts.items() if ts != set()]
        if len(conflicts) > 0:
            raise LL1ConflictError(f"Conflicts in Parse Table construction: {conflicts}")

        return table

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

        root = ParseNode(self.grammar.start_symbol)
        stack: Deque[Tuple[str, ParseNode]] = deque([(self._eof_symbol, None), (self.grammar.start_symbol, root)])

        while stack:
            stack_sym, node = stack.pop()

            if stack_sym in self.grammar.nonterminals:
                if token is None and self._top_down_table[stack_sym].get(self._eof_symbol) is None:
                    raise ParseError("Unexpected EOF")

                production: Production = self._top_down_table[stack_sym].get(token.type)

                if production is None:
                    expected = [t for t, p in self._top_down_table[stack_sym].items() if p is not None]
                    raise ParseError(f"Unexpected token '{token.lexeme}' at position {token.lineno}:{token.colno}. Expected one of {expected}")

                children_nodes = [ParseNode(sym) for sym in production.rhs]
                node.production = production
                node.children = children_nodes

                for sym_node in reversed(list(zip(production.rhs, children_nodes))):
                    stack.append(sym_node)

            elif stack_sym in self.grammar.terminals:
                if token is None or stack_sym != token.type:
                    raise ParseError(f"Unexpected token '{token.lexeme if token else 'EOF'}' at position {token.lineno}:{token.colno}. Expected '{stack_sym}'")

                node.token = token
                token = next(tokens, eof_token) # skip token

            elif stack_sym == self._eof_symbol:
                if token.type != self._eof_symbol:
                    raise ParseError(f"Extra token after parsing: '{token.lexeme}' at position {token.lineno}:{token.colno}.")
                break

        return root