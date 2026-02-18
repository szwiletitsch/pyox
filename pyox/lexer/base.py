from abc import ABC, abstractmethod
from typing import Iterator

from pyox.datatypes.LexToken import LexToken


class Lexer(ABC):
    """
    Abstract base class for all PyOx lexers.
    """

    @abstractmethod
    def tokenize(self, source: str) -> Iterator[LexToken]:
        """
        Convert source text into a stream of tokens.

        :param source: Input source code as a string.
        :return: Iterator over tokens.
        """
        raise NotImplementedError