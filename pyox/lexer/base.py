from abc import ABC, abstractmethod
from typing import Iterator, Any

from pyox.datatypes.LexToken import LexToken


class Lexer(ABC):
    """
    Abstract base class for all PyOx lexers.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """
        Base initializer to satisfy type checkers.
        Subclasses can accept their own parameters.
        """
        pass

    @abstractmethod
    def tokenize(self, source: str) -> Iterator[LexToken]:
        """
        Convert source text into a stream of tokens.

        :param source: Input source code as a string.
        :return: Iterator over tokens.
        """
        raise NotImplementedError