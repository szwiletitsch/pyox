from collections import defaultdict
from graphlib import TopologicalSorter, CycleError
from typing import Tuple, Dict, Set, List

from pyox.datatypes import ParseNode
from pyox.errors import PyOxAttributeEvaluationError
from pyox.grammar import SemanticRule


def evaluate_attribute_grammar(root: ParseNode) -> ParseNode:
    graph: Dict[Tuple[ParseNode, str], Set[Tuple[ParseNode, str]]] = defaultdict(set)
    rules: Dict[Tuple[ParseNode, str], Tuple[SemanticRule, List[ParseNode], int]] = {}

    # build dependency graph
    for node in root.walk():

        if not node.production:
            continue

        rule_env = [node, *node.children]

        for rule in node.production.semantic_rules:
            # validate that preset attributes are not overwritten
            for i, attr in rule.targets:
                if attr in rule_env[i].values:
                    raise PyOxAttributeEvaluationError(
                        f"Attribute ({rule_env[i]}, {attr}) already has value "
                        f"and would be overwritten by rule {rule}"
                    )

            targets = [(rule_env[i], attr) for i, attr in rule.targets]
            dependencies = {(rule_env[i], attr) for i, attr in rule.dependencies}

            for pos, target in enumerate(targets):
                if target in rules:
                    raise PyOxAttributeEvaluationError(f"Multiple assignments to attribute {target}; one of which in rule {rule}")

                graph[target] |= dependencies
                rules[target] = (rule, rule_env, pos)

            for dep in dependencies:
                graph.setdefault(dep, set())

    # sort dependency graph
    try:
        order = tuple(TopologicalSorter(graph).static_order())
    except CycleError as e:
        raise PyOxAttributeEvaluationError(f"{e} while evaluating attribute grammar") from e

    # evaluate attributes in sorted order
    for node, attr in order:
        rule_data = rules.get((node, attr))
        if rule_data:
            rule, rule_env, pos = rule_data

            try:
                res = rule.action(rule_env)
            except Exception as e:
                raise PyOxAttributeEvaluationError(
                    f"Semantic rule {rule} raised {e} while evaluating attribute grammar"
                ) from e

            if len(rule.targets) == 1:
                node.values[attr] = res
            else:
                if not isinstance(res, (list, tuple)):
                    raise PyOxAttributeEvaluationError(
                        f"Semantic rule {rule} must return a sequence "
                        f"of {len(rule.targets)} values"
                    )

                if len(res) != len(rule.targets):
                    raise PyOxAttributeEvaluationError(
                        f"Semantic rule {rule} returned {len(res)} values "
                        f"but defines {len(rule.targets)} targets"
                    )

                node.values[attr] = res[pos]

    return root
