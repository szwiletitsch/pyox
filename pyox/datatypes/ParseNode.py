from dataclasses import dataclass
from typing import Any, Optional, List


@dataclass
class ParseNode:
    """
    Represents a node in a parse tree for parsers.

    Attributes:
    -----------

    """
    symbol: str
    children: Optional[List[Any]] = None
    rule: Any = None        # todo revisit type
    values: Any = None      # todo revisit type

    def is_leaf(self) -> bool:
        """Return True if the node has no children."""
        return not self.children

    def add_child(self, child: Any) -> None:
        """Add a child to the parse tree."""
        self.children.append(child)