"""Shared local JSON/XML serialization contracts for query components."""

from __future__ import annotations

from abc import ABC, abstractmethod
from copy import deepcopy
from typing import TYPE_CHECKING, Literal
from xml.etree.ElementTree import Element

if TYPE_CHECKING:
    from mlclient.search.options import SearchOptions


def build_combined_query(
    search: dict,
    *,
    options: dict | SearchOptions | None = None,
    qtext: str | None = None,
) -> dict:
    """Combine native search criteria with inline options and a string query.

    Parameters
    ----------
    search : dict
        Native inner search members, such as query or ctsquery.
    options : dict | SearchOptions | None, default None
        Inline options members without an options wrapper, or their builder.
    qtext : str | None, default None
        Additional string query, AND-related to the native search criteria.

    Returns
    -------
    dict
        Independent JSON combined query, including copies of mutable inputs.

    Raises
    ------
    TypeError
        If options are not inline members or a SearchOptions builder, or qtext
        is neither a string nor None.
    """
    # Options import structured queries, so resolve their type after module loading.
    from mlclient.search.options import SearchOptions  # noqa: PLC0415

    if isinstance(options, SearchOptions):
        options = options.to_json()["options"]
    if options is not None and (not isinstance(options, dict) or "options" in options):
        message = (
            "options must be inline members without an options wrapper or SearchOptions"
        )
        raise TypeError(message)
    if qtext is not None and not isinstance(qtext, str):
        message = "qtext must be a string or None"
        raise TypeError(message)
    search = deepcopy(search)
    if options is not None:
        search["options"] = deepcopy(options)
    if qtext is not None:
        search["qtext"] = qtext
    return {"search": search}


class QueryComponent(ABC):
    """Serialize a query component locally in its native JSON or XML vocabulary.

    Concrete components define their own representation. This contract does not
    execute queries or imply XQuery compilation.
    """

    def serialize(
        self,
        output_format: Literal["json", "xml"] = "json",
    ) -> dict | Element:
        """Build a fresh native representation in the selected format.

        Parameters
        ----------
        output_format : {'json', 'xml'}, default 'json'
            Return a JSON-compatible dictionary or an ElementTree element.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh representation using the component's native vocabulary.

        Raises
        ------
        ValueError
            For unsupported formats or invalid component values.
        TypeError
            For arguments requiring server evaluation.
        """
        if output_format not in ("json", "xml"):
            message = "Query format must be json or xml."
            raise ValueError(message)
        return self._serialize(output_format)

    def to_json(self) -> dict:
        """Build native JSON directly from the component's values.

        Returns
        -------
        dict
            Fresh JSON component, without an intermediate XML representation.

        Raises
        ------
        ValueError
            For invalid component values.
        TypeError
            For arguments requiring server evaluation.
        """
        return self.serialize("json")

    def to_xml(self) -> Element:
        """Build native XML directly from the component's values.

        Returns
        -------
        xml.etree.ElementTree.Element
            Fresh native component, without an intermediate JSON representation.

        Raises
        ------
        ValueError
            For invalid component values.
        TypeError
            For arguments requiring server evaluation.
        """
        return self.serialize("xml")

    @abstractmethod
    def _serialize(self, output_format: Literal["json", "xml"]) -> dict | Element:
        """Describe this component using the selected independent serializer.

        Parameters
        ----------
        output_format : {'json', 'xml'}
            Requested native representation.

        Returns
        -------
        dict or xml.etree.ElementTree.Element
            Fresh native representation.
        """


class SearchQuery(QueryComponent):
    """A query that the REST Search API accepts as search criteria.

    Structured queries and CTS queries keep their own native vocabularies; both
    can be embedded in a combined query sent to /v1/search or /v1/values.
    """

    @abstractmethod
    def to_combined_query(
        self,
        *,
        options: dict | SearchOptions | None = None,
        qtext: str | None = None,
    ) -> dict:
        """Wrap this query in a JSON combined query.

        Parameters
        ----------
        options : dict | SearchOptions | None, default None
            Inline options members without an options wrapper, or their builder.
        qtext : str | None, default None
            Additional string query, AND-related to this query.

        Returns
        -------
        dict
            A fresh ``{"search": {...}}`` dictionary holding this query under
            the member the Search API expects for its vocabulary, with optional
            inline options and qtext. Accepted by ml.search operations.

        Raises
        ------
        ValueError
            For invalid query values.
        TypeError
            For arguments requiring server evaluation or unsupported options
            or qtext types.
        """
