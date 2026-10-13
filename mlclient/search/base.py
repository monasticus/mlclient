"""Shared local JSON/XML serialization contracts for query components."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Literal
from xml.etree.ElementTree import Element


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
    def to_combined_query(self) -> dict:
        """Wrap this query in a JSON combined query.

        Returns
        -------
        dict
            A fresh ``{"search": {...}}`` dictionary holding this query under
            the member the Search API expects for its vocabulary. Callers may
            add ``qtext`` or ``options`` members to the inner dictionary.

        Raises
        ------
        ValueError
            For invalid query values.
        TypeError
            For arguments requiring server evaluation.
        """
