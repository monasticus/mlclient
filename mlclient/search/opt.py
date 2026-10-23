"""Short constructors for immutable search options."""

from __future__ import annotations

from mlclient.search.options import (
    CollectionConstraint,
    ContainerConstraint,
    Control,
    NativeOptions,
    PageLength,
    Range,
    RangeConstraint,
    ReturnFacets,
    SearchOptions,
    SortOrder,
    Tuples,
    ValueConstraint,
    Values,
    WordConstraint,
)

__all__ = [
    "collection_constraint",
    "container_constraint",
    "control",
    "native",
    "options",
    "page_length",
    "range_",
    "range_constraint",
    "return_facets",
    "sort",
    "tuples",
    "value_constraint",
    "values",
    "word_constraint",
]

options = SearchOptions
range_ = Range
values = Values
tuples = Tuples
range_constraint = RangeConstraint
word_constraint = WordConstraint
value_constraint = ValueConstraint
collection_constraint = CollectionConstraint
container_constraint = ContainerConstraint
sort = SortOrder
control = Control
native = NativeOptions
page_length = PageLength
return_facets = ReturnFacets
