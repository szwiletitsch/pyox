from collections import deque
from typing import TypeAlias, Iterator, Deque, Tuple, cast

from pyox.datatypes import LexToken, ParseNode
from pyox.errors import ParseError
from pyox.grammar import Production
from pyox.parser import Parser


GotoTable: TypeAlias = dict[int, dict[str, int]]
ActionValue: TypeAlias = tuple[str] | tuple[str, Production]
ActionTable: TypeAlias = dict[int, dict[str, ActionValue]]


class LRParser(Parser):
    """
    Abstract LRParser class that only implements the actual parsing functionality.
    """

    def __init__(self, action_table: ActionTable, goto_table: GotoTable, eof_symbol: str = "$"):
        self._action_table = action_table
        self._goto_table = goto_table
        self._eof_symbol = eof_symbol


    def parse(self, tokens: Iterator[LexToken]) -> ParseNode:
        tokens = iter(tokens)
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
            action = self._action_table[state_id].get(token.type, ("error",))

            match action[0]:
                case "shift":
                    next_state = self._goto_table[state_id][token.type]

                    node = ParseNode(token.type)
                    node.token = token

                    stack.append((next_state, node))
                    token = next(tokens, eof_token) # skip

                case "reduce":
                    # ugly cast because static typechecker thinks action[1] could be a str
                    production = cast(Production, cast(object, action[1]))
                    lhs, rhs = production.lhs, production.rhs
                    node = ParseNode(lhs)
                    node.production = production

                    children = []
                    for _ in range(len(rhs)):
                        _, child = stack.pop()
                        children.append(child)

                    # children were popped in reverse
                    node.children = list(reversed(children))

                    state_after_pop, _ = stack[-1]
                    next_state = self._goto_table[state_after_pop][lhs]

                    stack.append((next_state, node))
                    continue

                case "accept":
                    break

                case "error":
                    expected = [t for t, p in self._action_table[state_id].items() if p is not None]
                    raise ParseError(f"Unexpected token '{token.lexeme}' at position {token.lineno}:{token.colno}. Expected one of {expected}")

        root = stack[-1][1]
        return root


