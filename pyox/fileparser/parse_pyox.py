from pyox.fileparser.ir_builder import build_lexer_rules, build_grammar
from pyox.fileparser.pyox_grammar import parse


def parse_pyox(source):
    parse_tree = parse(source)

    version, imports, lexer_root, parser_root = parse_tree.children

    # version_root.pretty_print() # todo
    # imports_root.pretty_print() # todo

    # lexer_root.pretty_print()
    lexer_rules = build_lexer_rules(lexer_root)
    grammar = build_grammar(parser_root)

    return lexer_rules, grammar



if __name__ == '__main__':
    import os
    def main() -> None:
        absolute_path = os.path.dirname(__file__)
        relative_path = "./../../example_grammars/calculator.pyox"
        full_path = os.path.join(absolute_path, relative_path)
        with open(full_path, "r") as f:
            source = f.read()


        lexer_rules, grammar = parse_pyox(source)
        print(lexer_rules)
        print(grammar)

    main()