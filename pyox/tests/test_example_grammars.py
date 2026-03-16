import functools
import unittest

from pyox.fileparser.parse_pyox import generate_fragments
from pyox.semantics import evaluate_attribute_grammar


CALCULATOR_GRAMMAR = "./example_grammars/calculator.pyox"

@functools.cache
def load_grammar(path):
    with open(path, "r") as f:
        source = f.read()

    return generate_fragments(source)

def evaluate(expression, grammar_path=CALCULATOR_GRAMMAR):
    lexer, parser = load_grammar(grammar_path)

    tokens = lexer.tokenize(expression)
    parse_tree = parser.parse(tokens)

    evaluate_attribute_grammar(parse_tree)

    parse_tree.pretty_print()

    return parse_tree.values["final"]


class TestGrammar(unittest.TestCase):
    def test_simple_expression(self):
        self.assertEqual(3, evaluate("1 + 2"))

    def test_imports(self):
        self.assertEqual(8, evaluate("2 ^ 3"))

    def test_precedence(self):
        self.assertEqual(5, evaluate("1 - 3 * 4 + 4 ^ 2"))

    def test_exponent_associativity(self):
        self.assertEqual(512, evaluate("2 ^ 3 ^ 2"))

    def test_whitespace(self):
        self.assertEqual(7, evaluate(" 1   +  \n\n\n\n  2 * 3 \n"))

    def test_invalid_expression(self):
        with self.assertRaises(Exception):
            evaluate("1 + * 2")