from typing import Tuple, Type

from pyox.fileparser.ir_builder import build_lexer_rules, build_grammar, build_imports, extract_version
from pyox.fileparser.pyox_grammar import parse
from pyox.lexer import Lexer
from pyox.lexer.lexer_impl.longest_input_match_lexer import LongestInputMatchLexer
from pyox.parser import SLR1Parser, Parser


def generate_fragments(
        source: str,
        lexer_type: Type[Lexer] = LongestInputMatchLexer,
        parser_type: Type[Parser] = SLR1Parser,
) -> Tuple[Lexer, Parser]:
    """
    Parse a .pyox source string and generate fully constructed lexer and parser.

    Args:
        source: The contents of a PyOx grammar file.
        lexer_type: The Lexer class to use (default: LongestInputMatchLexer).
        parser_type: The Parser class to use (default: SLR1Parser).

    Returns:
        A tuple (lexer, parser) where both are ready to tokenize and parse expressions.
    """

    parse_tree = parse(source)

    version_root, imports_root, lexer_root, parser_root = parse_tree.children

    version = extract_version(version_root)  # todo check versioning and warn user if files version and libraries version are different
    safe_globals = build_imports(imports_root)
    lexer_rules = build_lexer_rules(lexer_root)  # todo use safe globals for evaluating lexer converter
    grammar = build_grammar(parser_root, safe_globals)

    lexer = lexer_type(lexer_rules)
    parser = parser_type(grammar)

    return lexer, parser
