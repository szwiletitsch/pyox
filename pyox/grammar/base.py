from typing import Dict, List, Set


class Grammar:
    """
    Represents a context-free grammar and computes properties
    useful for parsers (FIRST, FOLLOW, nullable symbols).
    """

    def  __init__(self, start_symbol) -> None:
        self.start_symbol: str = start_symbol
        self.productions: Dict[str, List[List[str]]] = {}
        self.terminals: Set[str] = set()
        self.nonterminals: Set[str] = set()
        self.first_sets: Dict[str, Set[str]] = {}
        self.follow_sets: Dict[str, Set[str]] = {}
        self.nullable: Set[str] = set()

        self._eof_symbol = "$"

    def add_production(self, lhs: str, rhs: List[str]):
        """
        Add a production rule: lhs -> rhs
        Example: add_production("Expr", ["Term", "+", "Expr"])
        """
        if lhs not in self.productions:
            self.productions[lhs] = []
        self.productions[lhs].append(rhs)
        self.nonterminals.add(lhs)
        for symbol in rhs: # todo rethink if we want to enforce Terminals being lowercase and Nonterminals uppercase
            if not symbol.isupper():
                self.terminals.add(symbol)
            else:
                self.nonterminals.add(symbol)

    def compute_first_sets(self):
        self.first_sets = {symbol: set() for symbol in self.nonterminals | self.terminals}

        # first of terminal x is {x}
        for t in self.terminals:
            self.first_sets[t].add(t)

        changed = True
        while changed:
            changed = False
            for lhs, productions in self.productions.items():
                for rhs in productions:
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
            for lhs, productions in self.productions.items():
                for rhs in productions:
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