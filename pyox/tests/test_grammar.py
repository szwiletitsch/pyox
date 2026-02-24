import unittest

from pyox.grammar import Grammar

class TestGrammar(unittest.TestCase):
    def setUp(self):
        self.gram_simple = Grammar("EXPR")

        # EXPR
        self.gram_simple.add_production("EXPR", ["EXPR", "+", "TERM"])
        self.gram_simple.add_production("EXPR", ["EXPR", "-", "TERM"])
        self.gram_simple.add_production("EXPR", ["TERM"])

        # TERM
        self.gram_simple.add_production("TERM", ["TERM", "*", "FACTOR"])
        self.gram_simple.add_production("TERM", ["TERM", "/", "FACTOR"])
        self.gram_simple.add_production("TERM", ["FACTOR"])

        # FACTOR
        self.gram_simple.add_production("FACTOR", ["(", "EXPR", ")"])
        self.gram_simple.add_production("FACTOR", ["id"])


        self.gram_epsilon = Grammar("EXPR")

        # EXPR
        self.gram_epsilon.add_production("EXPR", ["TERM", "EXPRP"])

        # EXPR'
        self.gram_epsilon.add_production("EXPRP", ["+", "TERM", "EXPRP"])
        self.gram_epsilon.add_production("EXPRP", ["-", "TERM", "EXPRP"])
        self.gram_epsilon.add_production("EXPRP", [])

        # TERM
        self.gram_epsilon.add_production("TERM", ["FACTOR", "TERMP"])

        # TERM'
        self.gram_epsilon.add_production("TERMP", ["*", "FACTOR", "TERMP"])
        self.gram_epsilon.add_production("TERMP", ["/", "FACTOR", "TERMP"])
        self.gram_epsilon.add_production("TERMP", [])

        # FACTOR
        self.gram_epsilon.add_production("FACTOR", ["(", "EXPR", ")"])
        self.gram_epsilon.add_production("FACTOR", ["id"])



    def test_compute_first_sets(self):
        self.gram_simple.compute_first_sets()

        expected_first_sets = {
            '-': {'-'},
            'EXPR': {'id', '('},
            'TERM': {'id', '('},
            '+': {'+'},
            '*': {'*'},
            ')': {')'},
            '(': {'('},
            '/': {'/'},
            'id': {'id'},
            'FACTOR': {'id', '('}
        }

        self.assertEqual(expected_first_sets, self.gram_simple.first_sets)

    def test_compute_follow_sets(self):
        self.gram_simple.compute_follow_sets()

        expected_follow_sets = {
            'EXPR':   {')', '$', '+', '-'},
            'TERM':   {')', '$', '+', '-', '*', '/'},
            'FACTOR': {')', '$', '+', '-', '*', '/'}
        }

        self.assertEqual(self.gram_simple.follow_sets, expected_follow_sets)

    def test_compute_first_sets_with_epsilons(self):
        self.gram_epsilon.compute_first_sets()

        expected_first_sets = {
            '-': {'-'},
            '/': {'/'},
            'EXPRP': {'+', '-', 'ε'},
            'TERM': {'(', 'id'},
            'EXPR': {'(', 'id'},
            '*': {'*'}, '(': {'('},
            'FACTOR': {'(', 'id'},
            ')': {')'},
            'id': {'id'},
            '+': {'+'},
            'TERMP': {'*', '/', 'ε'}
        }

        self.assertEqual(expected_first_sets, self.gram_epsilon.first_sets)

    def test_compute_follow_sets_with_epsilons(self):
        self.gram_epsilon.compute_follow_sets()

        expected_follow_sets = {
            'TERMP': {'$', '+', '-', ')'},
            'EXPRP': {'$', ')'},
            'TERM': {'$', '+', '-', ')'},
            'FACTOR': {'+', '/', '$', '*', '-', ')'},
            'EXPR': {'$', ')'}
        }

        self.assertEqual(expected_follow_sets, self.gram_epsilon.follow_sets)

    def test_follow_computation_requires_trailer_algorithm(self):
        g = Grammar("A")

        g.add_production("A", ["B", "C", "D"])
        g.add_production("B", ["b"])
        g.add_production("C", [])  # nullable
        g.add_production("D", ["d"])

        g.compute_first_sets()
        g.compute_follow_sets()

        # Since C is nullable, B is effectively followed by D.
        # Therefore FIRST(D) = {'d'} must be in FOLLOW(B).
        expected_follow_b = {'d'}

        self.assertEqual(expected_follow_b, g.follow_sets["B"])

    def test_first_of_sequence_simple(self):
        self.gram_simple.compute_first_sets()

        # FIRST([FACTOR, "+"]) should be FIRST(FACTOR)
        result = self.gram_simple.first_of_sequence(["FACTOR", "+"])
        self.assertEqual(result, {"id", "("})

        # FIRST(["id"]) should be {"id"}
        result = self.gram_simple.first_of_sequence(["id"])
        self.assertEqual(result, {"id"})

        # FIRST(["(", "EXPR", ")"]) should be {"("}
        result = self.gram_simple.first_of_sequence(["(", "EXPR", ")"])
        self.assertEqual(result, {"("})

    def test_first_of_sequence_with_nullable(self):
        self.gram_epsilon.compute_first_sets()

        # EXPRP is nullable
        self.assertIn("ε", self.gram_epsilon.first_sets["EXPRP"])

        # FIRST(["EXPRP"]) should include ε
        result = self.gram_epsilon.first_of_sequence(["EXPRP"])
        self.assertEqual(result, {"+", "-", "ε"})

        # FIRST(["EXPRP", "TERM"])
        # Since EXPRP is nullable, FIRST should include FIRST(TERM)
        result = self.gram_epsilon.first_of_sequence(["EXPRP", "TERM"])
        self.assertEqual(result, {"+", "-", "(", "id"})

        # FIRST([]) should be {"ε"} (empty sequence is nullable)
        result = self.gram_epsilon.first_of_sequence([])
        self.assertEqual(result, {"ε"})

    def test_is_nullable_single_symbol(self):
        self.gram_epsilon.compute_first_sets()

        # EXPRP and TERMP are nullable
        self.assertTrue(self.gram_epsilon.is_nullable("EXPRP"))
        self.assertTrue(self.gram_epsilon.is_nullable("TERMP"))

        # TERM and FACTOR are not nullable
        self.assertFalse(self.gram_epsilon.is_nullable("TERM"))
        self.assertFalse(self.gram_epsilon.is_nullable("FACTOR"))

    def test_is_nullable_sequence(self):
        self.gram_epsilon.compute_first_sets()

        # EXPRP alone is nullable
        self.assertTrue(self.gram_epsilon.is_nullable(["EXPRP"]))

        # TERMP alone is nullable
        self.assertTrue(self.gram_epsilon.is_nullable(["TERMP"]))

        # EXPRP TERMP -> both nullable -> nullable
        self.assertTrue(self.gram_epsilon.is_nullable(["EXPRP", "TERMP"]))

        # EXPRP TERM -> TERM not nullable -> not nullable
        self.assertFalse(self.gram_epsilon.is_nullable(["EXPRP", "TERM"]))

        # Empty sequence -> nullable
        self.assertTrue(self.gram_epsilon.is_nullable([]))