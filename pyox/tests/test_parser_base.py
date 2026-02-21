from pyox.datatypes import LexToken
from pyox.grammar import Grammar
from pyox.parser import Parser


def make_tokens(types):
    for i, t in enumerate(types):
        yield LexToken(type=t, lexeme=t, lineno= 1, colno= i, start_index= -1, end_index= -1, value= -1)

def make_ll1_grammar():
    g = Grammar("EXPR")
    g.add_production("EXPR", ["id", "REST"])
    g.add_production("REST", ["+", "id", "REST"])
    g.add_production("REST", [])
    return g

def make_left_recursive_grammar():
    g = Grammar("E")
    g.add_production("E", ["E", "+", "T"])
    g.add_production("E", ["T"])
    g.add_production("T", ["id"])
    return g

def make_ambiguous_grammar():
    g = Grammar("S")
    g.add_production("S", ["S", "S"])
    g.add_production("S", ["a"])
    return g


class ParserTestBase:
    ParserClass = None
    ParserClassSupportsLeftRecursion = False
    ParserRequiresDeterministicGrammar = True

    def make_parser(self, grammar: Grammar) -> Parser:
        return self.ParserClass(grammar)

    def test_accepts_valid_expression_with_ll1_grammar(self):
        parser = self.make_parser(make_ll1_grammar())
        tokens = make_tokens(["id", "+", "id"])
        tree = parser.parse(tokens)
        self.assertEqual("EXPR", tree.symbol)

    def test_rejects_invalid_expression_with_ll1_grammar(self):
        parser = self.make_parser(make_ll1_grammar())
        tokens = make_tokens(["+"])
        with self.assertRaises(Exception):
            parser.parse(tokens)

    def test_handles_left_recursion(self):
        grammar = make_left_recursive_grammar()

        if self.ParserClassSupportsLeftRecursion:
            parser = self.make_parser(grammar)
            tokens = make_tokens(["id", "+", "id"])
            tree = parser.parse(tokens)
            self.assertEqual("E", tree.symbol)
        else:
            with self.assertRaises(Exception):
                parser = self.make_parser(grammar)

    def test_handles_ambiguous_grammar(self):
        grammar = make_ambiguous_grammar()

        if not self.ParserRequiresDeterministicGrammar:
            parser = self.make_parser(grammar)
            tokens = make_tokens(["a", "a", "a", "a", "a"])
            tree = parser.parse(tokens)
            self.assertEqual("S", tree.symbol)
        else:
            with self.assertRaises(Exception):
                parser = self.make_parser(grammar)