import unittest

from pyox.parser.parser_impl.slr_parser import SLR1Parser
from pyox.tests.test_parser_base import ParserTestBase


class TestParserSLR1(ParserTestBase, unittest.TestCase):
    ParserClass = SLR1Parser
    ParserClassSupportsLeftRecursion = True
    ParserRequiresDeterministicGrammar = True