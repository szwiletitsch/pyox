from pyox.fileparser.ir_builder import build_lexer_rules, build_grammar, build_imports, extract_version
from pyox.fileparser.pyox_grammar import parse


def parse_pyox(source):
    parse_tree = parse(source)

    version_root, imports_root, lexer_root, parser_root = parse_tree.children

    version = extract_version(version_root)
    safe_globals = build_imports(imports_root)
    lexer_rules = build_lexer_rules(lexer_root) # todo use safe globals for evaluating lexer converter
    grammar = build_grammar(parser_root, safe_globals)

    return version, safe_globals, lexer_rules, grammar



if __name__ == '__main__':
    import os
    def main() -> None:
        absolute_path = os.path.dirname(__file__)
        relative_path = "./../../example_grammars/calculator.pyox"
        full_path = os.path.join(absolute_path, relative_path)
        with open(full_path, "r") as f:
            source = f.read()


        version, safe_globals, lexer_rules, grammar = parse_pyox(source)

        print(version)
        print(safe_globals)
        print(lexer_rules)
        print(grammar)

    main()