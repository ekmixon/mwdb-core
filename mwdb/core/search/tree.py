import re
from luqum.tree import Item, Term, Phrase, FieldGroup


class QueryNode:
    def __init__(self, node: Item):
        self.node = node


class QueryValue(QueryNode):
    WILDCARD_MAP = {"*": "%", "?": "_"}

    @staticmethod
    def _unquote_phrase(node: Term, value: str):
        if isinstance(node, Phrase):
            return value[1:-1]
        else:
            return value

    def __init__(self, node: Term):
        super().__init__(node)
        self.value = self._unquote_phrase(node, node.value)
        self.unescaped_value = self._unquote_phrase(node, node.unescaped_value)
        self.has_wildcard = node.has_wildcard()
        self.anything = (self.value == "*")

    @property
    def sql_value(self):
        if self.has_wildcard:
            # Escape already contained SQL wildcards
            node_value = re.sub(r"([%_])", r"\\\1", self.value)
            # Transform unescaped Lucene wildcards to SQL form
            node_value = Term.WILDCARDS_PATTERN.sub(
                lambda m: self.WILDCARD_MAP[m.group(0)], node_value
            )
            # Unescape Lucene escaped special characters
            node_value = Term.WORD_ESCAPED_CHARS.sub(r"\1", node_value)
            return node_value
        else:
            return self.unescaped_value


class QueryRange:
    def __init__(self, node, low, high, include_low, include_high):
        pass


class QueryGroup:
    def __init__(self, node):
        pass


class QuerySearchField:
    def __init__(self, node, field, remainder, queried_type, value):
        pass


class QueryAndOperation:
    def __init__(self, node, operands):
        pass


class QueryOrOperation:
    def __init__(self, node, operands):
        pass


class QueryNotOperation:
    def __init__(self, node, operand):
        pass


class QuerySubquery:
    def __init__(self, node, field_mapper, expression):
        pass


class Subquery(FieldGroup):
    def __init__(self, expr, subquery):
        super().__init__(expr)
        self.subquery = subquery
