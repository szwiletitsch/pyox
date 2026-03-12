from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Iterator

from pyox.datatypes import LexToken
from pyox.grammar import Production


class WalkOrder(Enum):
    PRE = "pre"
    POST = "post"


@dataclass
class ParseNode:
    """
    Represents a node in a parse tree for parsers.
    """
    symbol: str
    children: List["ParseNode"] = field(default_factory=list)
    token: Optional[LexToken] = None
    production: Optional[Production] = None

    def __repr__(self):
        return f"ParseNode({self.symbol})"

    COLOR_RESET = "\033[0m"
    COLOR_NONTERM = "\033[94m"  # nonterm with children     -> blue
    COLOR_TERM = "\033[90m"     # nonterm without children  -> gray
    COLOR_TOKEN = "\033[32m"    # terminal                  -> green

    def pretty(self, prefix="", is_last=True):
        connector = "└── " if is_last else "├── "
        line = prefix + connector

        if self.token:
            line += f"{self.COLOR_TOKEN}{self.symbol + " : '" + str(self.token.value) + "'"}{self.COLOR_RESET}"
        elif self.children:
            line += f"{self.COLOR_NONTERM}{self.symbol}{self.COLOR_RESET}"
        else:
            line += f"{self.COLOR_TERM}{self.production}{self.COLOR_RESET}"

        lines = [line.replace("\n", "\\n")]

        new_prefix = prefix + ("    " if is_last else "│   ")

        for i, child in enumerate(self.children):
            is_child_last = i == len(self.children) - 1
            lines.append(child.pretty(new_prefix, is_child_last))

        return "\n".join(lines)

    def pretty_print(self):
        print(self.pretty())

    def walk(self, order: WalkOrder=WalkOrder.PRE) -> Iterator["ParseNode"]:
        if order is WalkOrder.PRE:
            yield self

        for child in self.children:
            yield from child.walk(order)

        if order is WalkOrder.POST:
            yield self

    def find(self, symbol: str, order: WalkOrder=WalkOrder.PRE) -> Iterator["ParseNode"]:
        for node in self.walk(order=order):
            if node.symbol == symbol:
                yield node

    def first(self, symbol: str, order=WalkOrder.PRE) -> "ParseNode | None":
        for node in self.walk(order=order):
            if node.symbol == symbol:
                return node
        return None