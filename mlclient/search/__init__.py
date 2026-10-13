"""Search API inputs: structured queries, search options and the query contract.

The package mirrors MarkLogic's search namespace
(http://marklogic.com/appservices/search) that structured queries and query
options belong to: mlclient.search.structured holds structured queries and their
sq builder, mlclient.search.options the search options builder. QueryComponent
and SearchQuery are the contracts every locally serialized query implements;
CTS queries implement them in mlclient.xquery, because they also compile to
XQuery. This package never imports mlclient.xquery.
"""

from mlclient.search.base import QueryComponent, SearchQuery

__all__ = [
    "QueryComponent",
    "SearchQuery",
]
