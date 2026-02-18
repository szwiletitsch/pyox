from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class LexToken:
    """
    Lex Token Datatype containing information about the lexeme such as type, lexical value, position
    """
    type: str
    lexeme: str
    lineno: int
    colno: int
    start_index: int
    end_index: int
    value: Any
