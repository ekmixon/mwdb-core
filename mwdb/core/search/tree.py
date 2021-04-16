import re
from typing import List, Union, Type
from luqum.tree import Item, Term, Phrase, FieldGroup, SearchField, Group
from .fields import BaseField

from mwdb.model import Object


class QueryNode:
    def __init__(self, node: Item):
        self.node = node


class QueryValue(QueryNode):
    pass


class QueryTerm(QueryValue):
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


class QueryRange(QueryValue):
    def __init__(self, node: Item, low: Union[QueryTerm, str], high: Union[QueryTerm, str],
                 include_low: bool = False, include_high: bool = False):
        super().__init__(node)
        self.low = low.value if isinstance(low, QueryTerm) else low
        self.high = high.value if isinstance(high, QueryTerm) else high
        self.include_low = include_low
        self.include_high = include_high

    @staticmethod
    def from_term(term: QueryTerm):
        if term.value.startswith(">="):
            value = term.value[2:]
            return QueryRange(
                node=term.node, low=value, high="*", include_low=True
            )
        elif term.value.startswith(">"):
            value = term.value[1:]
            return QueryRange(
                node=term.node, low=value, high="*"
            )
        elif term.value.startswith("<="):
            value = term.value[2:]
            return QueryRange(
                node=term.node, low="*", high=value, include_high=True
            )
        elif term.value.startswith("<"):
            value = term.value[1:]
            return QueryRange(
                node=term.node, low="*", high=value
            )
        else:
            return None


class QueryCondition(QueryNode):
    def get_condition(self):
        raise NotImplementedError


class QueryGroup(QueryCondition):
    def __init__(self, node: Group, condition: QueryCondition):
        super().__init__(node)
        self.condition = condition

    def get_condition(self):
        return self.condition.get_condition()


class QuerySearchField:
    def __init__(self, node: SearchField, field: BaseField, remainder: List[str], queried_type: Type[Object],
                 value: QueryValue):
        super().__init__(node)
        self.field = field
        self.remainder = remainder
        self.queried_type = queried_type
        self.value = value


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
