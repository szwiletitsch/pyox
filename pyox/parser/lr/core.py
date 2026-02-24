from dataclasses import dataclass
from typing import TypeAlias

from pyox.grammar import Production, Grammar

LR0ItemSet: TypeAlias = set["LR0Item"]

@dataclass(frozen=True)
class LR0Item:
    production: Production
    position: int

    def move(self):
        assert self.position < len(self.production.rhs)
        return LR0Item(self.production, self.position + 1)

    def is_reducible(self):
        return len(self.production.rhs) == self.position

    def __repr__(self):
        symbols = list(self.production.rhs)
        symbols.insert(self.position, ".")
        return f"{self.production.lhs} -> {' '.join(symbols)}"


def lr0_closure(grammar: Grammar, items: LR0ItemSet) -> set[LR0Item]:
    """
    Compute closure of a set of LR(0) items.
    """
    considered_items: LR0ItemSet = set()
    closure: LR0ItemSet = set()
    closure.update(items)

    changed = True
    while changed:
        changed = False

        length_b4 = len(closure)

        # consider only new items
        for item in closure - considered_items:
            considered_items.add(item)

            if not item.is_reducible():
                next_sym = item.production.rhs[item.position]
                if next_sym in grammar.nonterminals:
                    for production in grammar.productions_by_lhs[next_sym]:
                        new_item = LR0Item(production, 0)
                        closure.add(new_item)

        if length_b4 != len(closure):
            changed = True


    return closure