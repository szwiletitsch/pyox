import unittest

from pyox.parser.parser_impl.ll1_parser import LL1Parser
from pyox.tests.test_parser_base import ParserTestBase


class TestParserLL1(ParserTestBase, unittest.TestCase):
    ParserClass = LL1Parser
    ParserClassSupportsLeftRecursion = False
    ParserRequiresDeterministicGrammar = True