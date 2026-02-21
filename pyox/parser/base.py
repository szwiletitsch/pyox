from abc import ABC, abstractmethod
from typing import Iterator

from pyox.datatypes import LexToken, ParseNode


class Parser(ABC):
    """
    Abstract base class for all PyOx parsers.
    """

    @abstractmethod
    def parse(self, tokens: Iterator[LexToken]) -> ParseNode:
        """
        Parse a sequence of tokens and return an AST or result.

        :param tokens: Iterable of lexical tokens.
        :return: Parsed representation (e.g., AST).
        """
        raise NotImplementedError