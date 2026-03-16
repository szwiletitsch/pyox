from abc import ABC, abstractmethod
from typing import Iterator, Any

from pyox.datatypes import LexToken, ParseNode


class Parser(ABC):
    """
    Abstract base class for all PyOx parsers.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Base initializer to satisfy type checkers.
        Subclasses can accept their own parameters.
        """
        pass

    @abstractmethod
    def parse(self, tokens: Iterator[LexToken]) -> ParseNode:
        """
        Parse a sequence of tokens and return an AST or result.

        :param tokens: Iterable of lexical tokens.
        :return: Parsed representation (e.g., AST).
        """
        raise NotImplementedError