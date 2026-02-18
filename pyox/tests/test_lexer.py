import unittest
import re
from pyox.lexer.lexer_impl.longest_input_match_lexer import LongestInputMatchLexer

class TestLongestInputMatchLexer(unittest.TestCase):
    def setUp(self):
        # Define simple rules: INT > IDENT > PLUS > WHITESPACE
        self.rules = [
            (re.compile(r'\d+'), "INT", int),
            (re.compile(r'[a-zA-Z_]\w*'), "IDENT", lambda x: x),
            (re.compile(r'\+'), "PLUS", None),
            (re.compile(r'\s+'), "_", None),  # "_" type = skip
        ]
        self.lexer = LongestInputMatchLexer(self.rules)

    def test_basic_tokenization(self):
        source = "sum + 42"
        tokens = list(self.lexer.tokenize(source))

        expected = [
            ("IDENT", "sum"),
            ("PLUS", "+"),
            ("INT", 42),
        ]

        self.assertEqual(len(tokens), len(expected))

        for tok, (exp_type, exp_value) in zip(tokens, expected):
            self.assertEqual(tok.type, exp_type)
            self.assertEqual(tok.value, exp_value)

    def test_longest_match(self):
        # 'abc123' should match IDENT as one token, not IDENT + INT
        source = "abc123 + 7"
        tokens = list(self.lexer.tokenize(source))

        expected = [
            ("IDENT", "abc123"),
            ("PLUS", "+"),
            ("INT", 7),
        ]

        self.assertEqual(len(tokens), len(expected))

        for tok, (exp_type, exp_value) in zip(tokens, expected):
            self.assertEqual(tok.type, exp_type)
            self.assertEqual(tok.value, exp_value)

    def test_illegal_character(self):
        source = "sum$"
        with self.assertRaises(SyntaxError):
            list(self.lexer.tokenize(source))

    def test_include_ignored(self):
        source = "abc123 + 7"
        tokens = list(self.lexer.tokenize(source, include_ignored=True))

        expected = [
            ("IDENT", "abc123"),
            ("_", " "),
            ("PLUS", "+"),
            ("_", " "),
            ("INT", 7),
        ]

        self.assertEqual(len(tokens), len(expected))

        for tok, (exp_type, exp_value) in zip(tokens, expected):
            self.assertEqual(tok.type, exp_type)
            self.assertEqual(tok.value, exp_value)

    def test_newline_tokens(self):
        source = "a\nb"
        tokens = list(self.lexer.tokenize(source, include_ignored=True))
        expected_types = ["IDENT", "_", "IDENT"]
        self.assertEqual([t.type for t in tokens], expected_types)

        # expect b to be at line 2 col 1
        self.assertEqual(tokens[2].lineno, 2)
        self.assertEqual(tokens[2].colno, 1)

if __name__ == "__main__":
    unittest.main()