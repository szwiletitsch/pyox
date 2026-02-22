from dataclasses import dataclass, field
from typing import Any, Optional, List

from pyox.datatypes import LexToken
from pyox.grammar import Production


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

    def pretty(self, prefix="", is_last=True):
        connector = "└── " if is_last else "├── "
        line = prefix + connector + self.symbol

        if self.token:
            line += f" ({self.token.lexeme})"
        else:
            line += f" ({self.production})"

        lines = [line]

        new_prefix = prefix + ("    " if is_last else "│   ")

        for i, child in enumerate(self.children):
            is_child_last = i == len(self.children) - 1
            lines.append(child.pretty(new_prefix, is_child_last))

        return "\n".join(lines)

    def pretty_print(self):
        print(self.pretty())