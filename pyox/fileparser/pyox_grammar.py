import re

from pyox.grammar import Grammar
from pyox.lexer.lexer_impl.longest_input_match_lexer import LongestInputMatchLexer
from pyox.parser import SLR1Parser

_lexer = LongestInputMatchLexer([
    (re.compile(r'version'), "version", str),
    (re.compile(r'[0-9]+\.[0-9]+\.[0-9]+'), "version_num", str),
    (re.compile(r'section'), "section", str),
    (re.compile(r'preorder'), "preorder", str),
    (re.compile(r'postorder'), "postorder", str),
    (re.compile(r'IMPORTS'), "imports", str),
    (re.compile(r'LEXER'), "lexer", str),
    (re.compile(r'PARSER'), "parser", str),
    (re.compile(r':'), "colon", str),
    (re.compile(r'/((?![*+?])(?:[^\r\n\[/\\]|\\.|\[(?:[^\r\n\]\\]|\\.)*])+)/'), "regex", lambda x: re.compile(x[1:-1])),
    (re.compile(r'[a-z][a-z_]+'), "terminal", str),
    (re.compile(r'[A-Z][A-Z_]+'), "nonterminal", str),
    (re.compile(r'lambda [^\n]*'), "lambda", lambda x: eval(x)),
    (re.compile(r'_'), "ingored", str),
    (re.compile(r'@traversal'), "@traversal", str),
    (re.compile(r'=> [^|;]*'), "actions", str),
    (re.compile(r';'), "semicolon", str),
    (re.compile(r'\|'), "pipe", str),
    (re.compile(r'#[^\n]*'), "_", str),
    (re.compile(r'\s'), "_", str),
])

_g = Grammar("START")
_g.add_production("START", ["VERSION", "IMPORTS", "LEXER", "PARSER"])
_g.add_production("VERSION", ["version", "version_num"])

# imports
_g.add_production("IMPORTS", ["IMPORTS_HEAD", "IMPORTS_BODY"])
_g.add_production("IMPORTS_HEAD", ["section", "imports", "colon"])
_g.add_production("IMPORTS_BODY", []) # todo

# lexer
_g.add_production("LEXER", ["LEXER_HEAD", "LEXER_BODY"])
_g.add_production("LEXER_HEAD", ["section", "lexer", "colon"])
_g.add_production("LEXER_BODY", ["LEXER_RULES"])
_g.add_production("LEXER_RULES", ["LEXER_RULE", "LEXER_RULES"])
_g.add_production("LEXER_RULES", [])
_g.add_production("LEXER_RULE", ["regex", "LEX_SYM", "OPT_LAMBDA"])
_g.add_production("LEX_SYM", ["terminal"])
_g.add_production("LEX_SYM", ["ingored"])
_g.add_production("OPT_LAMBDA", ["lambda"])
_g.add_production("OPT_LAMBDA", [])

# parser
_g.add_production("PARSER", ["PARSER_HEAD", "PARSER_BODY"])
_g.add_production("PARSER_HEAD", ["section", "parser", "colon"])
_g.add_production("PARSER_BODY", ["PARSER_RULES"])
_g.add_production("PARSER_RULES", ["PARSER_RULE", "PARSER_RULES"])
_g.add_production("PARSER_RULES", [])
_g.add_production("PARSER_RULE", ["@traversal", "SYMBOL", "ORDER"])
_g.add_production("ORDER", ["preorder"])
_g.add_production("ORDER", ["postorder"])
_g.add_production("PARSER_RULE", ["nonterminal", "colon", "PRODUCTIONS", "semicolon"])
_g.add_production("PRODUCTIONS", ["PRODUCTION", "PRODUCTIONS_REST"])
_g.add_production("PRODUCTIONS_REST", ["pipe", "PRODUCTION", "PRODUCTIONS_REST"])
_g.add_production("PRODUCTIONS_REST", [])  # epsilon
_g.add_production("PRODUCTION", ["SYMBOLS", "OPT_ACTIONS"])
_g.add_production("SYMBOLS", ["SYMBOL", "SYMBOLS"])
_g.add_production("SYMBOLS", ["SYMBOL"])
_g.add_production("SYMBOL", ["terminal"])
_g.add_production("SYMBOL", ["nonterminal"])
_g.add_production("OPT_ACTIONS", ["actions"])
_g.add_production("OPT_ACTIONS", [])

_parser = SLR1Parser(_g)


def parse(source: str):
    return _parser.parse(_lexer.tokenize(source))