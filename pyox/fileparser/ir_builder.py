import re
from typing import Tuple, Callable, List

from pyox.datatypes import ParseNode
from pyox.errors import PyOxGrammarSyntaxError
from pyox.grammar import SemanticRule, Grammar
from pyox.lexer.lexer_impl.longest_input_match_lexer import Rule as LexerRule


def build_lexer_rules(lexer_root: ParseNode) -> List[LexerRule]:
    lexer_rule_nodes = lexer_root.find("LEXER_RULE") # flatten LEXER_RULE nodes in preorder

    lexer_rules: List[LexerRule] = []
    for node in lexer_rule_nodes:
        regex: re.Pattern = node.children[0].token.value
        name: str = node.children[1].children[0].token.value
        converter_node = node.children[2]
        converter: Callable[[str], any] = converter_node.children[0].token.value if converter_node.children else str

        lexer_rules.append((regex, name, converter))

    return lexer_rules

def parse_actions_str(actions_str: str) -> tuple[SemanticRule]:
    semantic_rules = []

    item_pattern = re.compile(r"\$(([1-9][0-9]*)|0)\.(\w*)")

    for action_str in actions_str.split("&&"):
        action_str = action_str.strip()
        if action_str.startswith("@"):
            continue # todo

        act_lhs, act_rhs = action_str.split("=", 1)

        targets = []
        for idx, _, attr in item_pattern.findall(act_lhs):
            targets.append((int(idx), attr))

        dependencies = set()
        for idx, _, attr in item_pattern.findall(act_rhs):
            dependencies.add((int(idx), attr))

        def _repl(m):
            _idx = m.group(1)
            _attr = m.group(3)
            return f"items[{_idx}].{_attr}"

        try:
            action = eval(f"lambda items: {item_pattern.sub(_repl, act_rhs)}")
        except SyntaxError:
            raise PyOxGrammarSyntaxError(f"Syntax error in action definition: '{action_str}'")

        semantic_rule = SemanticRule(
            tuple(targets),
            tuple(dependencies),
            action,
            action_str
        )

        semantic_rules.append(semantic_rule)

    return tuple(semantic_rules)


def build_grammar(parser_root: ParseNode) -> Grammar:
    grammar: Grammar = Grammar("START")

    for rule_node in parser_root.find("PARSER_RULE"):
        match rule_node.children[0].symbol:
            case "@traversal":      # traversal definition
                traversal_name: str = rule_node.children[1].children[0].token.value
                traversal_type: str = rule_node.children[2].children[0].token.value
                grammar.traversals.append((traversal_name, traversal_type))

            case "nonterminal":     # production definition
                lhs: str = rule_node.children[0].token.value
                for prod_node in rule_node.children[2].find("PRODUCTION"):
                    rhs = [sym_node.children[0].token.value for sym_node in prod_node.find("SYMBOL")]

                    semantic_rules: Tuple[SemanticRule] = tuple()
                    actions_tok = prod_node.children[1].children[0].token if prod_node.children[1].children else None
                    if actions_tok:
                        actions_str = actions_tok.value
                        actions_str = actions_str[2:] # remove leading '=>'
                        try:
                            semantic_rules = parse_actions_str(actions_str)
                        except PyOxGrammarSyntaxError as e:
                            raise PyOxGrammarSyntaxError(
                                f"{e} while parsing rule {lhs} -> {' '.join(rhs)} at position {actions_tok.lineno}:{actions_tok.colno}"
                            ) from e

                    grammar.add_production(lhs, rhs, semantic_rules)

    return grammar