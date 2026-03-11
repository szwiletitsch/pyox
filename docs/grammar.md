# Pyox Grammar File Guide

---

## File Structure / Sections

A `.pyox` file typically has three sections and follows this structure:

```text
version <version number>

section IMPORTS:
<python-style imports>

section LEXER:
<lexer rules>

section PARSER:
<parser rules>
```

Sections **must appear in this order**. More information about each section is below.

---

## Version

The version of a grammar file is defined in the first line:

```text
version <version number>
```

* `<version number>`: Major.Minor.Patch (e.g., `1.12.23`)
* Should match the version of the PyOx library used.

---

## IMPORTS Section

Optional Python imports for use in:

* Custom converters in the lexer section
* Semantic rules in the parser section

```text
section IMPORTS:
import math
import random
```

**Note:** This section must exist even if no imports are used.

---

## Lexer Section

A lexer rule is defined as:

```text
<regex> <name> [<converter>]
```

* `<regex>`: raw regex, e.g., `/\+/`
* `<name>`: token name (`_` for ignored tokens)
* `<converter>`: optional Python function (`Callable[[str], Any]`)

Example:

```text
section LEXER:
/\+/      plus
/\-/      minus
/-?[0-9]+/ num lambda x: int(x)
/\s/      _
```

**Important:**

* Uses Python `re` module; `/\+/` → `re.compile("\+")`
* Lexer uses **longest input match**; ties resolved by rule order
* Names must be lowercase
* `_` ignores the token
* Default converter is `str` if none is provided

---

## Parser Section

Comprises **traversal definitions** and **production definitions**.

Traversal definitions are suggested to appear first for readability.

### Symbol Naming Conventions

* Nonterminal names must be uppercase (e.g., EXPR, TERM)
* Terminal names must be lowercase, and have to be present in the names defined in the lexer section (e.g., `plus`, `num`)

---

### Traversals

```text
@traversal <name> (postorder | preorder | inorder)
```

Example:

```text
@traversal ast postorder
```

---

### Productions

```text
<NONTERMINAL>: <SYMBOL>* [=> <semantic actions>]
             [| ...]      # optional alternatives
             ;            # mandatory end
```

* Use `;` to end a production
* Use `|` to separate alternatives
* Empty RHS can be specified by omitting symbols

Example:

```text
EXPR: EXPR plus TERM
    | TERM
    ;
```

---

### Semantic Rules

Defined after the RHS of a production:

```text
<lhs>: <rhs> => <action> (&& <action>)* ;
```

* `$0` = LHS node, `$1`, `$2` = RHS nodes
* Multiple actions separated by `&&`, e.g., `$0.value = $1.value && @ast print($0.value)`
* Imported functions are available

Example:

```text
@traversal ast postorder
START: EXPR => $0.value = $1.value && @ast print($0.value)
     ;
```

**Note:** The sequences `;`, `|`, and `&&` cannot appear inside semantic rules.

---

## Best Practices

* Use `_` for ignored tokens (e.g., whitespace)
* Keep semantic actions concise
* Test incrementally with small grammar files
* Use consistent and clear token and nonterminal names

---

## Examples

See `example_grammars/` for ready-to-run `.pyox` files demonstrating all sections.

