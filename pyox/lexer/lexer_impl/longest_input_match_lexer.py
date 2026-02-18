import re
from typing import Iterable, Any, Tuple, Iterator, Callable, List
from ...lexer import Lexer
from ...datatypes.LexToken import LexToken


Rule = Tuple[
    re.Pattern,              # regex
    str,                     # token type
    Callable[[str], Any]     # value transformer
]
"""
Rule tuple format for LongestInputMatchLexer:
- pattern: compiled regex
- token_type: string identifier; '_' is ignored by default
- transformer: callable to convert lexeme to a value (e.g., int, float, str, or custom lambda); defaults to str (lexeme is copied into the value field)
"""

class LongestInputMatchLexer(Lexer):
    """
    Lexer implementation using the Longest-Input-Match (Maximal Munch) strategy.

    At each position in the input, this lexer tries all provided rules and selects
    the match with the longest lexeme. If multiple rules match the same length,
    the rule that appears first in the list is chosen.
    """

    def __init__(self, rules: Iterable[Rule]) -> None:
        self._rules: List[Rule] = list(rules)

    def tokenize(self, source: str, include_ignored: bool = False) -> Iterator[LexToken]:
        """
        Convert source code into a stream of tokens.

        :param source: str
            Input source code to tokenize.
        :param include_ignored: bool, default False
            If True, tokens with type '_' (ignored) are included in the output.
            Otherwise, they are skipped.

        :return: Iterator over included tokens.
        """

        index = 0
        lineno = 1
        colno = 1
        length = len(source)

        while index < length:
            longest_match = None
            longest_rule = None

            for pattern, token_type, transformer in self._rules:
                match = pattern.match(source, index)

                if match:
                    lexeme = match.group(0)
                    if longest_match is None or len(lexeme) > len(longest_match.group(0)):
                        longest_match = match
                        longest_rule = (pattern, token_type, transformer)

            if longest_match is None:
                raise SyntaxError(f"Illegal character at line {lineno}, column {colno}: '{source[index]}'")

            pattern, token_type, transformer = longest_rule
            lexeme = longest_match.group(0)
            start_index = index
            end_index = longest_match.end()
            value = transformer(lexeme) if transformer else lexeme

            if token_type != "_" or include_ignored:
                yield LexToken(
                    type=token_type,
                    lexeme=lexeme,
                    lineno=lineno,
                    colno=colno,
                    start_index=start_index,
                    end_index=end_index,
                    value=value
                )

            # update start position for next token
            for char in lexeme:
                if char == '\n':
                    lineno += 1
                    colno = 1
                else:
                    colno += 1
            index = end_index
