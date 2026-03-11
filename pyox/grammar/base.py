from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, Callable


@dataclass(frozen=True)
class SemanticRule:
    # (node_index, attribute_name)
    # 0 = LHS node, 1..n = RHS children
    targets: Tuple[Tuple[int, str], ...]
    # list of (node_index, attribute_name)
    dependencies: Tuple[Tuple[int, str], ...]
    action: Callable[[list], any]
    action_str: str

@dataclass(frozen=True)
class Production:
    lhs: str
    rhs: Tuple[str, ...]
    semantic_rules: Tuple[SemanticRule, ...] = field(default_factory=tuple)

    def __repr__(self) -> str:
        rhs_str = ' '.join(self.rhs) if len(self.rhs) > 0 else "ε"
        return f"{self.lhs} -> {rhs_str}"


class Grammar:
    """
    Represents a context-free grammar and computes properties
    useful for parsers (FIRST, FOLLOW, nullable symbols).
    """

    def  __init__(self, start_symbol) -> None:
        self.start_symbol: str = start_symbol
        self.productions: List[Production] = []
        self.productions_by_lhs: Dict[str, List[Production]] = defaultdict(list)
        self.terminals: Set[str] = set()
        self.nonterminals: Set[str] = set()
        self.first_sets: Dict[str, Set[str]] = {}
        self.follow_sets: Dict[str, Set[str]] = {}
        self.nullable: Set[str] = set()

        self._eof_symbol = "$"

    def __repr__(self):
        lines = [f"grammar (start: {self.start_symbol}): {{"]

        indent = 2
        productions_lines = [" " * indent + str(p) for p in self.productions]
        max_len = max(map(len, productions_lines))

        for i, (p_l, p) in enumerate(zip(productions_lines, self.productions)):
            if p.semantic_rules:
                actions = " && ".join(r.action_str for r in p.semantic_rules)
                productions_lines[i] = p_l.ljust(max_len + indent) + f"=> {actions}"

        lines.extend(productions_lines)
        lines.append("}")

        return "\n".join(lines)


    def add_production(self, lhs: str, rhs: List[str], semantic: Tuple[SemanticRule, ...] | None = None) -> None:
        """
        Add a production rule: lhs -> rhs
        Example: add_production("Expr", ["Term", "+", "Expr"])
        """
        if semantic is None:
            production = Production(lhs, tuple(rhs))
        else:
            production = Production(lhs, tuple(rhs), semantic)
        self.productions.append(production)
        self.productions_by_lhs[lhs].append(production)
        self.nonterminals.add(lhs)
        for symbol in rhs: # todo rethink if we want to enforce Terminals being lowercase and Nonterminals uppercase
            if not symbol.isupper():
                self.terminals.add(symbol)
            else:
                self.nonterminals.add(symbol)

    def compute_first_sets(self):
        self.first_sets = {symbol: set() for symbol in self.nonterminals | self.terminals | {self._eof_symbol}}

        # first of terminal x is {x}
        for t in self.terminals | {self._eof_symbol}:
            self.first_sets[t].add(t)

        changed = True
        while changed:
            changed = False
            for production in self.productions:
                lhs, rhs = production.lhs, production.rhs

                length_b4 = len(self.first_sets[lhs])

                for symbol in rhs:
                    self.first_sets[lhs] |= (self.first_sets[symbol] - {"ε"})
                    if "ε" not in self.first_sets[symbol]:
                        break
                else:
                    # if no break was performed, all symbols of rhs are nullable, therefore lhs is nullable
                    self.first_sets[lhs].add("ε")

                if len(self.first_sets[lhs]) != length_b4:
                    changed = True

    def compute_follow_sets(self):
        self.compute_first_sets()

        self.follow_sets = {n: set() for n in self.nonterminals}
        self.follow_sets[self.start_symbol].add(self._eof_symbol)

        changed = True
        while changed:
            changed = False
            for production in self.productions:
                lhs, rhs = production.lhs, production.rhs
                trailer = self.follow_sets[lhs].copy()

                for symbol in reversed(rhs):
                    if symbol in self.nonterminals:
                        b4 = len(self.follow_sets[symbol])
                        self.follow_sets[symbol] |= trailer
                        if len(self.follow_sets[symbol]) > b4:
                            changed = True

                        if "ε" in self.first_sets[symbol]:
                            trailer |= (self.first_sets[symbol] - {"ε"})
                        else:
                            trailer = self.first_sets[symbol] - {"ε"}
                    else:
                        trailer = {symbol}

    def first_of_sequence(self, beta: List[str]) -> Set[str]:
        first: Set[str] = set()
        for symbol in beta:
            symbol_first = self.first_sets[symbol]
            first |= self.first_sets[symbol] - {"ε"}
            if "ε" not in symbol_first:
                break
        else:
            first.add("ε")
        return first

    def is_nullable(self, beta: List[str] | str) -> bool:
        if type(beta) == str:
            return "ε" in self.first_sets[beta]
        elif type(beta) == list:
            return "ε" in self.first_of_sequence(beta)
        else:
            raise TypeError(f"Expected 'str' or 'list[str]' got {beta} instead")