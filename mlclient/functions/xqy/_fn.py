"""Native fn: expression builders for XQuery composition.

Arguments are data or XqyExpression trees. None passes the empty sequence; omitted
optional arguments retain the native function's context-dependent defaults.
XSLT-only and legacy functions retain their native context/dialect restrictions.
"""

from __future__ import annotations

import datetime

from mlclient._experimental import experimental
from mlclient._options import UNSET
from mlclient.functions.xqy.expressions import XqyExpression, FunctionCall


def _optional_call(name: str, *arguments) -> FunctionCall:
    """Trim omitted trailing arguments; preserve explicit empty sequences.

    Parameters
    ----------
    name : str
        Native function name.
    arguments : str | int | float | bool | XqyExpression | None
        Native positional arguments; UNSET marks an omitted optional slot.

    Returns
    -------
    FunctionCall
        Call with interior omissions represented by empty sequences.
    """
    end = len(arguments)
    while end and arguments[end - 1] is UNSET:
        end -= 1
    return FunctionCall(
        name,
        tuple(None if arg is UNSET else arg for arg in arguments[:end]),
    )


@experimental()
class Fn:
    """Pure fn: builders; native context and dialect requirements still apply."""

    @staticmethod
    def abs(arg: float | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the absolute value of $arg.

        Parameters
        ----------
        arg : float | XqyExpression | None
            A numeric value.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:abs``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:abs
        """
        return FunctionCall("fn:abs", (arg,))

    @staticmethod
    def adjust_date_to_timezone(
        arg: datetime.date | XqyExpression | None,
        *,
        timezone: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Adjusts an xs:date value to a specific timezone, or to no timezone at all.

        Parameters
        ----------
        arg : datetime.date | XqyExpression | None
            The date to adjust to the new timezone.
        timezone : str | XqyExpression | None
            The new timezone for the date.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:adjust-date-to-timezone``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:adjust-date-to-timezone
        """
        return _optional_call("fn:adjust-date-to-timezone", arg, timezone)

    @staticmethod
    def adjust_date_time_to_timezone(
        arg: datetime.datetime | XqyExpression | None,
        *,
        timezone: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Adjusts an xs:dateTime value to a specific timezone, or to no timezone at all.

        Parameters
        ----------
        arg : datetime.datetime | XqyExpression | None
            The dateTime to adjust to the new timezone.
        timezone : str | XqyExpression | None
            The new timezone for the dateTime.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:adjust-dateTime-to-timezone``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:adjust-dateTime-to-timezone
        """
        return _optional_call("fn:adjust-dateTime-to-timezone", arg, timezone)

    @staticmethod
    def adjust_time_to_timezone(
        arg: datetime.time | XqyExpression | None,
        *,
        timezone: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Adjusts an xs:time value to a specific timezone, or to no timezone at all.

        Parameters
        ----------
        arg : datetime.time | XqyExpression | None
            The time to adjust to the new timezone.
        timezone : str | XqyExpression | None
            The new timezone for the date.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:adjust-time-to-timezone``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:adjust-time-to-timezone
        """
        return _optional_call("fn:adjust-time-to-timezone", arg, timezone)

    @staticmethod
    def analyze_string(
        in_: str | XqyExpression | None,
        regex: str | XqyExpression,
        *,
        flags: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        The result of the function is a new element node whose string value is the
        original string, but which contains markup to show which parts of the input
        match the regular expression.

        Parameters
        ----------
        in_ : str | XqyExpression | None
            The string to start with.
        regex : str | XqyExpression
            The regular expression pattern to match.
        flags : str | XqyExpression | None
            The flag representing how to interpret the regular expression. One of "s",
            "m", "i", or "x", as defined in http://www.w3.org/TR/xpath-functions/#flags
            .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:analyze-string``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:analyze-string
        """
        return _optional_call("fn:analyze-string", in_, regex, flags)

    @staticmethod
    def avg(
        arg: str
        | int
        | float
        | bool
        | list[str | int | float | bool]
        | XqyExpression
        | list[XqyExpression]
        | None,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the average of the values in the input sequence $arg, that is, the sum
        of the values divided by the number of values.

        Parameters
        ----------
        arg : str | int | float | bool | list[str | int | float | bool] | XqyExpression | list[XqyExpression] | None
            The sequence of values to average.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:avg``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:avg
        """
        return FunctionCall("fn:avg", (arg,))

    @staticmethod
    def base_uri(arg: XqyExpression | None = UNSET) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the value of the base-uri property for the specified node.

        Parameters
        ----------
        arg : XqyExpression | None
            The node whose base-uri is to be returned.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:base-uri``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:base-uri
        """
        return _optional_call("fn:base-uri", arg)

    @staticmethod
    def boolean(
        arg: XqyExpression | list[XqyExpression] | None,
        *,
        collation: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Computes the effective boolean value of the sequence $arg.

        Parameters
        ----------
        arg : XqyExpression | list[XqyExpression] | None
            A sequence of items.
        collation : str | XqyExpression | None
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:boolean``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:boolean
        """
        return _optional_call("fn:boolean", arg, collation)

    @staticmethod
    def ceiling(arg: float | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the smallest (closest to negative infinity) number with no fractional
        part that is not less than the value of $arg.

        Parameters
        ----------
        arg : float | XqyExpression | None
            A numeric value.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:ceiling``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:ceiling
        """
        return FunctionCall("fn:ceiling", (arg,))

    @staticmethod
    def codepoint_equal(
        comparand1: str | XqyExpression | None,
        comparand2: str | XqyExpression | None,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns true if the specified parameters are the same Unicode code point,
        otherwise returns false.

        Parameters
        ----------
        comparand1 : str | XqyExpression | None
            A string to be compared.
        comparand2 : str | XqyExpression | None
            A string to be compared.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:codepoint-equal``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:codepoint-equal
        """
        return FunctionCall("fn:codepoint-equal", (comparand1, comparand2))

    @staticmethod
    def codepoints_to_string(
        arg: int | list[int] | XqyExpression | list[XqyExpression] | None,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Creates an xs:string from a sequence of Unicode code points.

        Parameters
        ----------
        arg : int | list[int] | XqyExpression | list[XqyExpression] | None
            A sequence of Unicode code points.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:codepoints-to-string``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:codepoints-to-string
        """
        return FunctionCall("fn:codepoints-to-string", (arg,))

    @staticmethod
    def collection(
        uri: str | list[str] | XqyExpression | list[XqyExpression] | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns all of the documents that belong to the specified collection(s).

        Parameters
        ----------
        uri : str | list[str] | XqyExpression | list[XqyExpression] | None
            The URI of the collection to retrieve. If you omit this parameter, returns
            all of the documents in the database. If you specify a list of URIs, returns
            all of the documents in all of the collections at the URIs specified in the
            list.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:collection``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:collection
        """
        return _optional_call("fn:collection", uri)

    @staticmethod
    def compare(
        comparand1: str | XqyExpression | None,
        comparand2: str | XqyExpression | None,
        *,
        collation: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns -1, 0, or 1, depending on whether the value of the $comparand1 is
        respectively less than, equal to, or greater than the value of $comparand2,
        according to the rules of the collation that is used.

        Parameters
        ----------
        comparand1 : str | XqyExpression | None
            A string to be compared.
        comparand2 : str | XqyExpression | None
            A string to be compared.
        collation : str | XqyExpression | None
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:compare``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:compare
        """
        return _optional_call("fn:compare", comparand1, comparand2, collation)

    @staticmethod
    def concat(
        parameter1: str | int | float | bool | XqyExpression | None,
        *parameters: str | int | float | bool | XqyExpression,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the xs:string that is the concatenation of the values of the specified
        parameters.

        Parameters
        ----------
        parameter1 : str | int | float | bool | XqyExpression | None
            A value.
        parameters : str | int | float | bool | XqyExpression
            A value.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:concat``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:concat
        """
        return FunctionCall("fn:concat", (parameter1, *parameters))

    @staticmethod
    def contains(
        parameter1: str | XqyExpression | None,
        parameter2: str | XqyExpression | None,
        *,
        collation: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns true if the first parameter contains the string from the second
        parameter, otherwise returns false.

        Parameters
        ----------
        parameter1 : str | XqyExpression | None
            The string from which to test.
        parameter2 : str | XqyExpression | None
            The string to test for existence in the first parameter.
        collation : str | XqyExpression | None
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:contains``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:contains
        """
        return _optional_call("fn:contains", parameter1, parameter2, collation)

    @staticmethod
    def count(
        sequence: XqyExpression | list[XqyExpression] | None,
        *,
        maximum: float | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the number of items in the value of $arg.

        Parameters
        ----------
        sequence : XqyExpression | list[XqyExpression] | None
            The sequence of items to count.
        maximum : float | XqyExpression | None
            The maximum value of the count to return. MarkLogic Server will stop count
            when the $maximum value is reached and return the $maximum value. This is an
            extension to the W3C standard fn:count function.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:count``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:count
        """
        return _optional_call("fn:count", sequence, maximum)

    @staticmethod
    def current() -> FunctionCall:
        """Build a native XQuery expression.

        Returns the item that was the context item at the point where the expression was
        invoked from the XSLT stylesheet.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:current``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:current
        """
        return FunctionCall("fn:current")

    @staticmethod
    def current_date() -> FunctionCall:
        """Build a native XQuery expression.

        Returns xs:date(fn:current-dateTime()).

        Returns
        -------
        FunctionCall
            Composable call to ``fn:current-date``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:current-date
        """
        return FunctionCall("fn:current-date")

    @staticmethod
    def current_date_time() -> FunctionCall:
        """Build a native XQuery expression.

        Returns the current dateTime value (with timezone) from the dynamic context.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:current-dateTime``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:current-dateTime
        """
        return FunctionCall("fn:current-dateTime")

    @staticmethod
    def current_group() -> FunctionCall:
        """Build a native XQuery expression.

        Returns the current regex group.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:current-group``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:current-group
        """
        return FunctionCall("fn:current-group")

    @staticmethod
    def current_grouping_key() -> FunctionCall:
        """Build a native XQuery expression.

        Returns the current regex grouping key.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:current-grouping-key``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:current-grouping-key
        """
        return FunctionCall("fn:current-grouping-key")

    @staticmethod
    def current_time() -> FunctionCall:
        """Build a native XQuery expression.

        Returns xs:time(fn:current-dateTime()).

        Returns
        -------
        FunctionCall
            Composable call to ``fn:current-time``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:current-time
        """
        return FunctionCall("fn:current-time")

    @staticmethod
    def data(arg: XqyExpression | list[XqyExpression] | None) -> FunctionCall:
        """Build a native XQuery expression.

        Takes a sequence of items and returns a sequence of atomic values.

        Parameters
        ----------
        arg : XqyExpression | list[XqyExpression] | None
            The items whose typed values are to be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:data``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:data
        """
        return FunctionCall("fn:data", (arg,))

    @staticmethod
    def date_time(
        arg1: datetime.date | XqyExpression,
        arg2: datetime.time | XqyExpression,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:dateTime value created by combining an xs:date and an xs:time.

        Parameters
        ----------
        arg1 : datetime.date | XqyExpression
            The date to be combined with the time argument.
        arg2 : datetime.time | XqyExpression
            The time to be combined with the date argument.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:dateTime``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:dateTime
        """
        return FunctionCall("fn:dateTime", (arg1, arg2))

    @staticmethod
    def day_from_date(arg: datetime.date | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:integer between 1 and 31, both inclusive, representing the day
        component in the localized value of $arg.

        Parameters
        ----------
        arg : datetime.date | XqyExpression | None
            The date whose day component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:day-from-date``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:day-from-date
        """
        return FunctionCall("fn:day-from-date", (arg,))

    @staticmethod
    def day_from_date_time(
        arg: datetime.datetime | XqyExpression | None,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:integer between 1 and 31, both inclusive, representing the day
        component in the localized value of $arg.

        Parameters
        ----------
        arg : datetime.datetime | XqyExpression | None
            The dateTime whose day component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:day-from-dateTime``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:day-from-dateTime
        """
        return FunctionCall("fn:day-from-dateTime", (arg,))

    @staticmethod
    def days_from_duration(arg: str | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:integer representing the days component in the canonical lexical
        representation of the value of $arg.

        Parameters
        ----------
        arg : str | XqyExpression | None
            The duration whose day component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:days-from-duration``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:days-from-duration
        """
        return FunctionCall("fn:days-from-duration", (arg,))

    @staticmethod
    def deep_equal(
        parameter1: XqyExpression | list[XqyExpression] | None,
        parameter2: XqyExpression | list[XqyExpression] | None,
        *,
        collation: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        This function assesses whether two sequences are deep-equal to each other.

        Parameters
        ----------
        parameter1 : XqyExpression | list[XqyExpression] | None
            The first sequence of items, each item should be an atomic value or node.
        parameter2 : XqyExpression | list[XqyExpression] | None
            The sequence of items to compare to the first sequence of items, again each
            item should be an atomic value or node.
        collation : str | XqyExpression | None
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:deep-equal``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:deep-equal
        """
        return _optional_call("fn:deep-equal", parameter1, parameter2, collation)

    @staticmethod
    def default_collation() -> FunctionCall:
        """Build a native XQuery expression.

        Returns the value of the default collation property from the static context.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:default-collation``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:default-collation
        """
        return FunctionCall("fn:default-collation")

    @staticmethod
    def distinct_nodes(
        nodes: XqyExpression | list[XqyExpression] | None,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        [0.9-ml only] Returns the sequence resulting from removing from the input
        sequence all but one of a set of nodes that have the same identity as one
        another.

        Parameters
        ----------
        nodes : XqyExpression | list[XqyExpression] | None
            A sequence of nodes from which to eliminate duplicate nodes (nodes with the
            same identity) so that only one node of each identity remains.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:distinct-nodes``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:distinct-nodes
        """
        return FunctionCall("fn:distinct-nodes", (nodes,))

    @staticmethod
    def distinct_values(
        arg: XqyExpression | list[XqyExpression] | None,
        *,
        collation: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the sequence that results from removing from $arg all but one of a set
        of values that are eq to one other.

        Parameters
        ----------
        arg : XqyExpression | list[XqyExpression] | None
            A sequence of items.
        collation : str | XqyExpression | None
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:distinct-values``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:distinct-values
        """
        return _optional_call("fn:distinct-values", arg, collation)

    @staticmethod
    def doc(
        uri: str | list[str] | XqyExpression | list[XqyExpression] | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the document(s) stored in the database at the specified URI(s).

        Parameters
        ----------
        uri : str | list[str] | XqyExpression | list[XqyExpression] | None
            The URI of the document to retrieve. If you omit this parameter, returns all
            of the documents in the database - this is only allowed if you're not using
            xquery version 1.0 strict. If you specify a list of URIs, returns all of the
            documents at the URIs specified in the list.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:doc``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:doc
        """
        return _optional_call("fn:doc", uri)

    @staticmethod
    def doc_available(uri: str | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        If fn:doc($uri) returns a document node, this function returns true.

        Parameters
        ----------
        uri : str | XqyExpression | None
            The URI of the document to check.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:doc-available``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:doc-available
        """
        return FunctionCall("fn:doc-available", (uri,))

    @staticmethod
    def document(
        uris: XqyExpression | list[XqyExpression] | None,
        *,
        base_node: XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the document(s) stored in the database at the specified URI(s).

        Parameters
        ----------
        uris : XqyExpression | list[XqyExpression] | None
            The $uris is a sequence of the URI(s) of the document(s) to be retrieved.
            This parameter is mandatory. However you may pass a singleton sequence with
            an empty string in it. In that case it will return the stylesheet that
            contains this function call when called from XSLT stylesheet and all the
            documents in the database when called from XQuery- this is allowed only when
            you are not using version 1.0 strict. If any URI in this sequence is an
            absolute URI, then it is used as is. If it is a relative URI, it is resolved
            against a base URI specified in the second argument.
        base_node : XqyExpression | None
            If $base-node is supplied, its base URI is used to resolve relative URIs in
            uri-sequence. If it is not supplied, the base URI of the node that contained
            the fn:document() call is used.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:document``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:document
        """
        return _optional_call("fn:document", uris, base_node)

    @staticmethod
    def document_uri(arg: XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the value of the document-uri property for the specified node.

        Parameters
        ----------
        arg : XqyExpression | None
            The node whose document-uri is to be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:document-uri``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:document-uri
        """
        return FunctionCall("fn:document-uri", (arg,))

    @staticmethod
    def element_available(element_name: str | XqyExpression) -> FunctionCall:
        """Build a native XQuery expression.

        Returns true if and only if the name of an XSLT instruction is passed in.

        Parameters
        ----------
        element_name : str | XqyExpression
            The name of the element to test.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:element-available``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:element-available
        """
        return FunctionCall("fn:element-available", (element_name,))

    @staticmethod
    def empty(sequence: XqyExpression | list[XqyExpression] | None) -> FunctionCall:
        """Build a native XQuery expression.

        If the value of $arg is the empty sequence, the function returns true;
        otherwise, the function returns false.

        Parameters
        ----------
        sequence : XqyExpression | list[XqyExpression] | None
            A sequence to test.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:empty``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:empty
        """
        return FunctionCall("fn:empty", (sequence,))

    @staticmethod
    def encode_for_uri(uri_part: str | XqyExpression) -> FunctionCall:
        """Build a native XQuery expression.

        Invertible function that escapes characters required to be escaped inside path
        segments of URIs.

        Parameters
        ----------
        uri_part : str | XqyExpression
            A string representing an unescaped URI.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:encode-for-uri``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:encode-for-uri
        """
        return FunctionCall("fn:encode-for-uri", (uri_part,))

    @staticmethod
    def ends_with(
        parameter1: str | XqyExpression | None,
        parameter2: str | XqyExpression | None,
        *,
        collation: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns true if the first parameter ends with the string from the second
        parameter, otherwise returns false.

        Parameters
        ----------
        parameter1 : str | XqyExpression | None
            The parameter from which to test.
        parameter2 : str | XqyExpression | None
            The string to test whether it is at the end of the first parameter.
        collation : str | XqyExpression | None
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:ends-with``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:ends-with
        """
        return _optional_call("fn:ends-with", parameter1, parameter2, collation)

    @staticmethod
    def error(
        error: XqyExpression | None = UNSET,
        description: str | XqyExpression | None = UNSET,
        data: XqyExpression | list[XqyExpression] | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        [1.0 and 1.0-ml only, 0.9-ml has a different signature] Throw the given error.

        Parameters
        ----------
        error : XqyExpression | None
            Error code, as an xs:QName . Note that this parameter does not exist in
            0.9-ml.
            Omit to use the native default; None explicitly passes ().
        description : str | XqyExpression | None
            String description to be printed with the error.
            Omit to use the native default; None explicitly passes ().
        data : XqyExpression | list[XqyExpression] | None
            Parameters to the error message.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:error``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:error
        """
        return _optional_call("fn:error", error, description, data)

    @staticmethod
    def escape_html_uri(uri_part: str | XqyExpression) -> FunctionCall:
        """Build a native XQuery expression.

        %-escapes everything except printable ASCII characters.

        Parameters
        ----------
        uri_part : str | XqyExpression
            A string representing an unescaped URI.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:escape-html-uri``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:escape-html-uri
        """
        return FunctionCall("fn:escape-html-uri", (uri_part,))

    @staticmethod
    def escape_uri(
        uri_part: str | XqyExpression,
        escape_reserved: bool | XqyExpression,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        This is a May 2003 function, and is only available in compatibility mode (XQuery
        0.9-ML)--it has been replaced with fn:encode-for-uri, fn:iri-to-uri, and
        fn:escape-html-uri.

        Parameters
        ----------
        uri_part : str | XqyExpression
            A string representing an unescaped URI.
        escape_reserved : bool | XqyExpression
            Specify a boolean value of true to return an escaped URI or a boolean value
            of false to return an unescaped URI.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:escape-uri``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:escape-uri
        """
        return FunctionCall("fn:escape-uri", (uri_part, escape_reserved))

    @staticmethod
    def exactly_one(arg: XqyExpression | list[XqyExpression] | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns $arg if it contains exactly one item.

        Parameters
        ----------
        arg : XqyExpression | list[XqyExpression] | None
            The sequence of items.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:exactly-one``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:exactly-one
        """
        return FunctionCall("fn:exactly-one", (arg,))

    @staticmethod
    def exists(sequence: XqyExpression | list[XqyExpression] | None) -> FunctionCall:
        """Build a native XQuery expression.

        If the value of $arg is not the empty sequence, the function returns true;
        otherwise, the function returns false.

        Parameters
        ----------
        sequence : XqyExpression | list[XqyExpression] | None
            A sequence to test.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:exists``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:exists
        """
        return FunctionCall("fn:exists", (sequence,))

    @staticmethod
    def expanded_qname(
        param_uri: str | XqyExpression | None,
        param_local: str | XqyExpression,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        [0.9-ml only, use fn:QName instead] Returns an xs:QName with the namespace URI
        given in $paramURI and the local name in $paramLocal.

        Parameters
        ----------
        param_uri : str | XqyExpression | None
            A namespace URI, as a string.
        param_local : str | XqyExpression
            A localname, as a string.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:expanded-QName``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:expanded-QName
        """
        return FunctionCall("fn:expanded-QName", (param_uri, param_local))

    @staticmethod
    def false() -> FunctionCall:
        """Build a native XQuery expression.

        Returns the xs:boolean value false.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:false``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:false
        """
        return FunctionCall("fn:false")

    @staticmethod
    def filter(
        function: XqyExpression,
        seq: XqyExpression | list[XqyExpression] | None,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns those items from the sequence $seq for which the supplied function
        $function returns true.

        Parameters
        ----------
        function : XqyExpression
            The function value.
        seq : XqyExpression | list[XqyExpression] | None
            The function value.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:filter``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:filter
        """
        return FunctionCall("fn:filter", (function, seq))

    @staticmethod
    def floor(arg: float | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the largest (closest to positive infinity) number with no fractional
        part that is not greater than the value of $arg.

        Parameters
        ----------
        arg : float | XqyExpression | None
            A numeric value.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:floor``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:floor
        """
        return FunctionCall("fn:floor", (arg,))

    @staticmethod
    def fold_left(
        function: XqyExpression | list[XqyExpression] | None,
        zero: XqyExpression | list[XqyExpression] | None,
        seq: XqyExpression | list[XqyExpression] | None,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Processes the supplied sequence from left to right, applying the supplied
        function repeatedly to each item in turn, together with an accumulated result
        value.

        Parameters
        ----------
        function : XqyExpression | list[XqyExpression] | None
            The fold function value.
        zero : XqyExpression | list[XqyExpression] | None
            The zero argument.
        seq : XqyExpression | list[XqyExpression] | None
            The sequence to fold

        Returns
        -------
        FunctionCall
            Composable call to ``fn:fold-left``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:fold-left
        """
        return FunctionCall("fn:fold-left", (function, zero, seq))

    @staticmethod
    def fold_right(
        function: XqyExpression | list[XqyExpression] | None,
        zero: XqyExpression | list[XqyExpression] | None,
        seq: XqyExpression | list[XqyExpression] | None,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Processes the supplied sequence from right to left, applying the supplied
        function repeatedly to each item in turn, together with an accumulated result
        value.

        Parameters
        ----------
        function : XqyExpression | list[XqyExpression] | None
            The fold function value.
        zero : XqyExpression | list[XqyExpression] | None
            The zero argument.
        seq : XqyExpression | list[XqyExpression] | None
            The sequence to fold

        Returns
        -------
        FunctionCall
            Composable call to ``fn:fold-right``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:fold-right
        """
        return FunctionCall("fn:fold-right", (function, zero, seq))

    @staticmethod
    def format_date(
        value: datetime.date | XqyExpression,
        picture: str | XqyExpression,
        *,
        language: str | XqyExpression | None = UNSET,
        calendar: str | XqyExpression | None = UNSET,
        country: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns a formatted date value based on the picture argument.

        Parameters
        ----------
        value : datetime.date | XqyExpression
            The given date $value that needs to be formatted.
        picture : str | XqyExpression
            The desired string representation of the given date $value . The picture
            string is a sequence of characters, in which the characters represent
            variables such as, decimal-separator-sign, grouping-sign, zero-digit-sign,
            digit-sign, pattern-separator, percent sign and per-mille-sign. For details
            on the picture string, see http://www.w3.org/TR/xslt20/#date-picture-string
            .
        language : str | XqyExpression | None
            The desired language for string representation of the date $value .
            Omit to use the native default; None explicitly passes ().
        calendar : str | XqyExpression | None
            The only calendar supported at this point is "Gregorian" or "AD".
            Omit to use the native default; None explicitly passes ().
        country : str | XqyExpression | None
            $country is used the specification to take into account country specific
            string representation.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:format-date``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:format-date
        """
        return _optional_call(
            "fn:format-date",
            value,
            picture,
            language,
            calendar,
            country,
        )

    @staticmethod
    def format_date_time(
        value: datetime.datetime | XqyExpression,
        picture: str | XqyExpression,
        *,
        language: str | XqyExpression | None = UNSET,
        calendar: str | XqyExpression | None = UNSET,
        country: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns a formatted dateTime value based on the picture argument.

        Parameters
        ----------
        value : datetime.datetime | XqyExpression
            The given dateTime $value that needs to be formatted.
        picture : str | XqyExpression
            The desired string representation of the given dateTime $value . The picture
            string is a sequence of characters, in which the characters represent
            variables such as, decimal-separator-sign, grouping-sign, zero-digit-sign,
            digit-sign, pattern-separator, percent sign and per-mille-sign. For details
            on the picture string, see http://www.w3.org/TR/xslt20/#date-picture-string
            .
        language : str | XqyExpression | None
            The desired language for string representation of the dateTime $value .
            Omit to use the native default; None explicitly passes ().
        calendar : str | XqyExpression | None
            The only calendar supported at this point is "Gregorian" or "AD".
            Omit to use the native default; None explicitly passes ().
        country : str | XqyExpression | None
            $country is used the specification to take into account country specific
            string representation.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:format-dateTime``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:format-dateTime
        """
        return _optional_call(
            "fn:format-dateTime",
            value,
            picture,
            language,
            calendar,
            country,
        )

    @staticmethod
    def format_number(
        value: float | XqyExpression,
        picture: str | XqyExpression,
        *,
        decimal_format_name: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns a formatted string representation of value argument based on the
        supplied picture.

        Parameters
        ----------
        value : float | XqyExpression
            The given numeric $value that needs to be formatted.
        picture : str | XqyExpression
            The desired string representation of the given number $value . The picture
            string is a sequence of characters, in which the characters represent
            variables such as, decimal-separator-sign, grouping-sign, zero-digit-sign,
            digit-sign, pattern-separator, percent sign and per-mille-sign. For details
            on the format-number picture string, see
            http://www.w3.org/TR/xslt20/#function-format-number .
        decimal_format_name : str | XqyExpression | None
            Represents a named <xsl:decimal-format> instruction. It is used to assign
            values to the variables mentioned above based on the picture string.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:format-number``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:format-number
        """
        return _optional_call("fn:format-number", value, picture, decimal_format_name)

    @staticmethod
    def format_time(
        value: datetime.time | XqyExpression,
        picture: str | XqyExpression,
        *,
        language: str | XqyExpression | None = UNSET,
        calendar: str | XqyExpression | None = UNSET,
        country: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns a formatted time value based on the picture argument.

        Parameters
        ----------
        value : datetime.time | XqyExpression
            The given time $value that needs to be formatted.
        picture : str | XqyExpression
            The desired string representation of the given time $value . The picture
            string is a sequence of characters, in which the characters represent
            variables such as, decimal-separator-sign, grouping-sign, zero-digit-sign,
            digit-sign, pattern-separator, percent sign and per-mille-sign. For details
            on the picture string, see http://www.w3.org/TR/xslt20/#date-picture-string
            .
        language : str | XqyExpression | None
            The desired language for string representation of the time $value .
            Omit to use the native default; None explicitly passes ().
        calendar : str | XqyExpression | None
            The only calendar supported at this point is "Gregorian" or "AD".
            Omit to use the native default; None explicitly passes ().
        country : str | XqyExpression | None
            $country is used the specification to take into account country specific
            string representation.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:format-time``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:format-time
        """
        return _optional_call(
            "fn:format-time",
            value,
            picture,
            language,
            calendar,
            country,
        )

    @staticmethod
    def function_arity(function: XqyExpression) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the arity of the function(s) that the argument refers to.

        Parameters
        ----------
        function : XqyExpression
            The function value.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:function-arity``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:function-arity
        """
        return FunctionCall("fn:function-arity", (function,))

    @staticmethod
    def function_available(
        function_name: str | XqyExpression,
        *,
        arity: int | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns true if and only if there is an XQuery or XSLT function whose name and
        optionally arity matches the value of the $function-name and the optional $arity
        arguments.

        Parameters
        ----------
        function_name : str | XqyExpression
            The $function-name is a string containing a lexical QName. It may be a name
            of a builtin-type, type imported using xsl:import-schema, or an extension
            type. This parameter is mandatory. The lexical QName is expanded using the
            namespace declarations in scope for the expression. If the lexical QName is
            unprefixed, then the standard function namespace is used in the expanded
            QName.
        arity : int | XqyExpression | None
            If $arity parameter is present, then the function returns true if and only
            if the function specified by the first argument has a signature that takes
            $arity number of arguments.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:function-available``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:function-available
        """
        return _optional_call("fn:function-available", function_name, arity)

    @staticmethod
    def function_lookup(
        name: XqyExpression,
        arity: int | XqyExpression,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns a function with the given name and arity, or the empty sequence if none
        exists.

        Parameters
        ----------
        name : XqyExpression
            The QName of the function.
        arity : int | XqyExpression
            The number of arguments the function takes.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:function-lookup``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:function-lookup
        """
        return FunctionCall("fn:function-lookup", (name, arity))

    @staticmethod
    def function_name(function: XqyExpression) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the QName of the function(s) that the argument refers to.

        Parameters
        ----------
        function : XqyExpression
            The function value.
            ---

        Returns
        -------
        FunctionCall
            Composable call to ``fn:function-name``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:function-name
        """
        return FunctionCall("fn:function-name", (function,))

    @staticmethod
    def generate_id(node: XqyExpression | None = UNSET) -> FunctionCall:
        """Build a native XQuery expression.

        Returns a string that uniquely identifies a given node.

        Parameters
        ----------
        node : XqyExpression | None
            The node whose ID will be generated.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:generate-id``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:generate-id
        """
        return _optional_call("fn:generate-id", node)

    @staticmethod
    def head(seq: XqyExpression | list[XqyExpression] | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the first item in a sequence.

        Parameters
        ----------
        seq : XqyExpression | list[XqyExpression] | None
            A sequence of items.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:head``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:head
        """
        return FunctionCall("fn:head", (seq,))

    @staticmethod
    def hours_from_date_time(
        arg: datetime.datetime | XqyExpression | None,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:integer between 0 and 23, both inclusive, representing the hours
        component in the localized value of $arg.

        Parameters
        ----------
        arg : datetime.datetime | XqyExpression | None
            The dateTime whose hours component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:hours-from-dateTime``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:hours-from-dateTime
        """
        return FunctionCall("fn:hours-from-dateTime", (arg,))

    @staticmethod
    def hours_from_duration(arg: str | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:integer representing the hours component in the canonical lexical
        representation of the value of $arg.

        Parameters
        ----------
        arg : str | XqyExpression | None
            The duration whose hour component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:hours-from-duration``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:hours-from-duration
        """
        return FunctionCall("fn:hours-from-duration", (arg,))

    @staticmethod
    def hours_from_time(arg: datetime.time | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:integer between 0 and 23, both inclusive, representing the value
        of the hours component in the localized value of $arg.

        Parameters
        ----------
        arg : datetime.time | XqyExpression | None
            The time whose hours component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:hours-from-time``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:hours-from-time
        """
        return FunctionCall("fn:hours-from-time", (arg,))

    @staticmethod
    def id(
        arg: str | list[str] | XqyExpression | list[XqyExpression] | None,
        *,
        node: XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the sequence of element nodes that have an ID value matching the value
        of one or more of the IDREF values supplied in $arg.

        Parameters
        ----------
        arg : str | list[str] | XqyExpression | list[XqyExpression] | None
            The IDs of the elements to return.
        node : XqyExpression | None
            The target node.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:id``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:id
        """
        return _optional_call("fn:id", arg, node)

    @staticmethod
    def idref(
        arg: str | list[str] | XqyExpression | list[XqyExpression] | None,
        *,
        node: XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the sequence of element or attribute nodes that have an IDREF value
        matching the value of one or more of the ID values supplied in $arg.

        Parameters
        ----------
        arg : str | list[str] | XqyExpression | list[XqyExpression] | None
            The IDREFs of the elements and attributes to return.
        node : XqyExpression | None
            The target node.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:idref``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:idref
        """
        return _optional_call("fn:idref", arg, node)

    @staticmethod
    def implicit_timezone() -> FunctionCall:
        """Build a native XQuery expression.

        Returns the value of the implicit timezone property from the dynamic context.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:implicit-timezone``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:implicit-timezone
        """
        return FunctionCall("fn:implicit-timezone")

    @staticmethod
    def in_scope_prefixes(element: XqyExpression) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the prefixes of the in-scope namespaces for $element.

        Parameters
        ----------
        element : XqyExpression
            The element whose in-scope prefixes will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:in-scope-prefixes``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:in-scope-prefixes
        """
        return FunctionCall("fn:in-scope-prefixes", (element,))

    @staticmethod
    def index_of(
        seq_param: str
        | int
        | float
        | bool
        | list[str | int | float | bool]
        | XqyExpression
        | list[XqyExpression]
        | None,
        srch_param: str | int | float | bool | XqyExpression,
        *,
        collation_literal: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns a sequence of positive integers giving the positions within the sequence
        $seqParam of items that are equal to $srchParam.

        Parameters
        ----------
        seq_param : str | int | float | bool | list[str | int | float | bool] | XqyExpression | list[XqyExpression] | None
            A sequence of values.
        srch_param : str | int | float | bool | XqyExpression
            A value to find on the list.
        collation_literal : str | XqyExpression | None
            A collation identifier.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:index-of``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:index-of
        """
        return _optional_call("fn:index-of", seq_param, srch_param, collation_literal)

    @staticmethod
    def insert_before(
        target: XqyExpression | list[XqyExpression] | None,
        position: int | XqyExpression,
        inserts: XqyExpression | list[XqyExpression] | None,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns a new sequence constructed from the value of $target with the value of
        $inserts inserted at the position specified by the value of $position.

        Parameters
        ----------
        target : XqyExpression | list[XqyExpression] | None
            The sequence of items into which new items will be inserted.
        position : int | XqyExpression
            The position in the target sequence at which the new items will be added.
        inserts : XqyExpression | list[XqyExpression] | None
            The items to insert into the target sequence.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:insert-before``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:insert-before
        """
        return FunctionCall("fn:insert-before", (target, position, inserts))

    @staticmethod
    def iri_to_uri(uri_part: str | XqyExpression) -> FunctionCall:
        """Build a native XQuery expression.

        Idempotent function that escapes non-URI characters.

        Parameters
        ----------
        uri_part : str | XqyExpression
            A string representing an unescaped URI.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:iri-to-uri``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:iri-to-uri
        """
        return FunctionCall("fn:iri-to-uri", (uri_part,))

    @staticmethod
    def key(
        key_name: str | XqyExpression,
        key_value: str | XqyExpression,
        *,
        top: XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        The key function does for keys what the id function does for IDs.

        Parameters
        ----------
        key_name : str | XqyExpression
            The name of the key.
        key_value : str | XqyExpression
            The value of the key.
        top : XqyExpression | None
            The subtree to limit the results to.
            ---
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:key``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:key
        """
        return _optional_call("fn:key", key_name, key_value, top)

    @staticmethod
    def lang(
        testlang: str | XqyExpression | None,
        *,
        node: XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        This function tests whether the language of $node, or the context node if the
        second argument is omitted, as specified by xml:lang attributes is the same as,
        or is a sublanguage of, the language specified by $testlang.

        Parameters
        ----------
        testlang : str | XqyExpression | None
            The language against which to test the node.
        node : XqyExpression | None
            The node to test.
            ---
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:lang``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:lang
        """
        return _optional_call("fn:lang", testlang, node)

    @staticmethod
    def last() -> FunctionCall:
        """Build a native XQuery expression.

        Returns the context size from the dynamic context.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:last``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:last
        """
        return FunctionCall("fn:last")

    @staticmethod
    def local_name(arg: XqyExpression | None = UNSET) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the local part of the name of $arg as an xs:string that will either be
        the zero-length string or will have the lexical form of an xs:NCName.

        Parameters
        ----------
        arg : XqyExpression | None
            The node whose local name is to be returned.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:local-name``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:local-name
        """
        return _optional_call("fn:local-name", arg)

    @staticmethod
    def local_name_from_qname(arg: XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:NCName representing the local part of $arg.

        Parameters
        ----------
        arg : XqyExpression | None
            A qualified name.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:local-name-from-QName``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:local-name-from-QName
        """
        return FunctionCall("fn:local-name-from-QName", (arg,))

    @staticmethod
    def lower_case(string: str | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the specified string converting all of the characters to lower-case
        characters.

        Parameters
        ----------
        string : str | XqyExpression | None
            The string to convert.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:lower-case``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:lower-case
        """
        return FunctionCall("fn:lower-case", (string,))

    @staticmethod
    def map(
        function: XqyExpression | list[XqyExpression] | None,
        seq: XqyExpression | list[XqyExpression] | None,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Applies the function item $function to every item from the sequence $seq in
        turn, returning the concatenation of the resulting sequences in order.

        Parameters
        ----------
        function : XqyExpression | list[XqyExpression] | None
            The function value.
        seq : XqyExpression | list[XqyExpression] | None
            The function value.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:map``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:map
        """
        return FunctionCall("fn:map", (function, seq))

    @staticmethod
    def map_pairs(
        function: XqyExpression | list[XqyExpression] | None,
        seq1: XqyExpression | list[XqyExpression] | None,
        seq2: XqyExpression | list[XqyExpression] | None,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Applies the function item $function to successive pairs of items taken one from
        $seq1 and one from $seq2, returning the concatenation of the resulting sequences
        in order.

        Parameters
        ----------
        function : XqyExpression | list[XqyExpression] | None
            The map function value.
        seq1 : XqyExpression | list[XqyExpression] | None
            The first sequence argument.
        seq2 : XqyExpression | list[XqyExpression] | None
            The second sequence argument.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:map-pairs``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:map-pairs
        """
        return FunctionCall("fn:map-pairs", (function, seq1, seq2))

    @staticmethod
    def matches(
        input: str | XqyExpression | None,
        pattern: str | XqyExpression,
        *,
        flags: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns true if the specified $input matches the specified $pattern, otherwise
        returns false.

        Parameters
        ----------
        input : str | XqyExpression | None
            The input from which to match.
        pattern : str | XqyExpression
            The regular expression to match.
        flags : str | XqyExpression | None
            The flag representing how to interpret the regular expression. One of "s",
            "m", "i", or "x", as defined in http://www.w3.org/TR/xpath-functions/#flags
            .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:matches``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:matches
        """
        return _optional_call("fn:matches", input, pattern, flags)

    @staticmethod
    def max(
        arg: str
        | int
        | float
        | bool
        | list[str | int | float | bool]
        | XqyExpression
        | list[XqyExpression]
        | None,
        *,
        collation: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Selects an item from the input sequence $arg whose value is greater than or
        equal to the value of every other item in the input sequence.

        Parameters
        ----------
        arg : str | int | float | bool | list[str | int | float | bool] | XqyExpression | list[XqyExpression] | None
            The sequence of values whose maximum will be returned.
        collation : str | XqyExpression | None
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:max``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:max
        """
        return _optional_call("fn:max", arg, collation)

    @staticmethod
    def min(
        arg: str
        | int
        | float
        | bool
        | list[str | int | float | bool]
        | XqyExpression
        | list[XqyExpression]
        | None,
        *,
        collation: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Selects an item from the input sequence $arg whose value is less than or equal
        to the value of every other item in the input sequence.

        Parameters
        ----------
        arg : str | int | float | bool | list[str | int | float | bool] | XqyExpression | list[XqyExpression] | None
            The sequence of values whose minimum will be returned.
        collation : str | XqyExpression | None
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:min``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:min
        """
        return _optional_call("fn:min", arg, collation)

    @staticmethod
    def minutes_from_date_time(
        arg: datetime.datetime | XqyExpression | None,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:integer value between 0 and 59, both inclusive, representing the
        minute component in the localized value of $arg.

        Parameters
        ----------
        arg : datetime.datetime | XqyExpression | None
            The dateTime whose minutes component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:minutes-from-dateTime``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:minutes-from-dateTime
        """
        return FunctionCall("fn:minutes-from-dateTime", (arg,))

    @staticmethod
    def minutes_from_duration(arg: str | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:integer representing the minutes component in the canonical
        lexical representation of the value of $arg.

        Parameters
        ----------
        arg : str | XqyExpression | None
            The duration whose minute component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:minutes-from-duration``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:minutes-from-duration
        """
        return FunctionCall("fn:minutes-from-duration", (arg,))

    @staticmethod
    def minutes_from_time(arg: datetime.time | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:integer value between 0 to 59, both inclusive, representing the
        value of the minutes component in the localized value of $arg.

        Parameters
        ----------
        arg : datetime.time | XqyExpression | None
            The time whose minutes component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:minutes-from-time``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:minutes-from-time
        """
        return FunctionCall("fn:minutes-from-time", (arg,))

    @staticmethod
    def month_from_date(arg: datetime.date | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:integer between 1 and 12, both inclusive, representing the month
        component in the localized value of $arg.

        Parameters
        ----------
        arg : datetime.date | XqyExpression | None
            The date whose month component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:month-from-date``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:month-from-date
        """
        return FunctionCall("fn:month-from-date", (arg,))

    @staticmethod
    def month_from_date_time(
        arg: datetime.datetime | XqyExpression | None,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:integer between 1 and 12, both inclusive, representing the month
        component in the localized value of $arg.

        Parameters
        ----------
        arg : datetime.datetime | XqyExpression | None
            The dateTime whose month component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:month-from-dateTime``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:month-from-dateTime
        """
        return FunctionCall("fn:month-from-dateTime", (arg,))

    @staticmethod
    def months_from_duration(arg: str | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:integer representing the months component in the canonical lexical
        representation of the value of $arg.

        Parameters
        ----------
        arg : str | XqyExpression | None
            The duration whose month component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:months-from-duration``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:months-from-duration
        """
        return FunctionCall("fn:months-from-duration", (arg,))

    @staticmethod
    def name(arg: XqyExpression | None = UNSET) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the name of a node, as an xs:string that is either the zero-length
        string, or has the lexical form of an xs:QName.

        Parameters
        ----------
        arg : XqyExpression | None
            The node whose name is to be returned.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:name``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:name
        """
        return _optional_call("fn:name", arg)

    @staticmethod
    def namespace_uri(arg: XqyExpression | None = UNSET) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the namespace URI of the xs:QName of the node specified by $arg.

        Parameters
        ----------
        arg : XqyExpression | None
            The node whose namespace URI is to be returned.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:namespace-uri``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:namespace-uri
        """
        return _optional_call("fn:namespace-uri", arg)

    @staticmethod
    def namespace_uri_for_prefix(
        prefix: str | XqyExpression | None,
        element: XqyExpression,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the namespace URI of one of the in-scope namespaces for $element,
        identified by its namespace prefix.

        Parameters
        ----------
        prefix : str | XqyExpression | None
            A namespace prefix to look up.
        element : XqyExpression
            An element node providing namespace context.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:namespace-uri-for-prefix``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:namespace-uri-for-prefix
        """
        return FunctionCall("fn:namespace-uri-for-prefix", (prefix, element))

    @staticmethod
    def namespace_uri_from_qname(arg: XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the namespace URI for $arg as an xs:string.

        Parameters
        ----------
        arg : XqyExpression | None
            A qualified name.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:namespace-uri-from-QName``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:namespace-uri-from-QName
        """
        return FunctionCall("fn:namespace-uri-from-QName", (arg,))

    @staticmethod
    def nilled(arg: XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Summary: Returns an xs:boolean indicating whether the argument node is "nilled".

        Parameters
        ----------
        arg : XqyExpression | None
            The node to test for nilled status.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:nilled``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:nilled
        """
        return FunctionCall("fn:nilled", (arg,))

    @staticmethod
    def node_kind(node: XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        [0.9-ml only, use xdmp:node-kind in 1.0 and 1.0-ml] Returns an xs:string
        representing the node's kind: either "document", "element", "attribute", "text",
        "namespace", "processing-instruction", "binary", or "comment".

        Parameters
        ----------
        node : XqyExpression | None
            The node whose kind is to be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:node-kind``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:node-kind
        """
        return FunctionCall("fn:node-kind", (node,))

    @staticmethod
    def node_name(arg: XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an expanded-QName for node kinds that can have names.

        Parameters
        ----------
        arg : XqyExpression | None
            The node whose name is to be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:node-name``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:node-name
        """
        return FunctionCall("fn:node-name", (arg,))

    @staticmethod
    def normalize_space(input: str | XqyExpression | None = UNSET) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the specified string with normalized whitespace, which strips off any
        leading or trailing whitespace and replaces any other sequences of more than one
        whitespace characters with a single space character (#x20).

        Parameters
        ----------
        input : str | XqyExpression | None
            The string from which to normalize whitespace.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:normalize-space``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:normalize-space
        """
        return _optional_call("fn:normalize-space", input)

    @staticmethod
    def normalize_unicode(
        arg: str | XqyExpression | None,
        *,
        normalization_form: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Return the argument normalized according to the normalization criteria for a
        normalization form identified by the value of $normalizationForm.

        Parameters
        ----------
        arg : str | XqyExpression | None
            The string to normalize.
        normalization_form : str | XqyExpression | None
            The form under which to normalize the specified string: NFC, NFD, NFKC, or
            NFKD.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:normalize-unicode``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:normalize-unicode
        """
        return _optional_call("fn:normalize-unicode", arg, normalization_form)

    @staticmethod
    def not_(arg: XqyExpression | list[XqyExpression] | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns true if the effective boolean value is false, and false if the effective
        boolean value is true.

        Parameters
        ----------
        arg : XqyExpression | list[XqyExpression] | None
            The expression to negate.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:not``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:not
        """
        return FunctionCall("fn:not", (arg,))

    @staticmethod
    def number(
        arg: str | int | float | bool | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the value indicated by $arg or, if $arg is not specified, the context
        item after atomization, converted to an xs:double.

        Parameters
        ----------
        arg : str | int | float | bool | XqyExpression | None
            The value to be returned as an xs:double value.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:number``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:number
        """
        return _optional_call("fn:number", arg)

    @staticmethod
    def one_or_more(arg: XqyExpression | list[XqyExpression] | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns $arg if it contains one or more items.

        Parameters
        ----------
        arg : XqyExpression | list[XqyExpression] | None
            The sequence of items.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:one-or-more``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:one-or-more
        """
        return FunctionCall("fn:one-or-more", (arg,))

    @staticmethod
    def position() -> FunctionCall:
        """Build a native XQuery expression.

        Returns the context position from the dynamic context.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:position``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:position
        """
        return FunctionCall("fn:position")

    @staticmethod
    def prefix_from_qname(arg: XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:NCName representing the prefix of $arg.

        Parameters
        ----------
        arg : XqyExpression | None
            A qualified name.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:prefix-from-QName``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:prefix-from-QName
        """
        return FunctionCall("fn:prefix-from-QName", (arg,))

    @staticmethod
    def qname(
        uri: str | XqyExpression | None,
        lexical: str | XqyExpression,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:QName with the namespace URI given in $paramURI.

        Parameters
        ----------
        uri : str | XqyExpression | None
            A namespace URI, as a string.
        lexical : str | XqyExpression
            A lexical qualified name (xs:QName), a string of the form "prefix:localname"
            or "localname".

        Returns
        -------
        FunctionCall
            Composable call to ``fn:QName``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:QName
        """
        return FunctionCall("fn:QName", (uri, lexical))

    @staticmethod
    def regex_group(group_number: int | XqyExpression) -> FunctionCall:
        """Build a native XQuery expression.

        While the xsl:matching-substring instruction is active, a set of current
        captured substrings is available, corresponding to the parenthesized sub-
        expressions of the regular expression.

        Parameters
        ----------
        group_number : int | XqyExpression
            The group number to return.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:regex-group``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:regex-group
        """
        return FunctionCall("fn:regex-group", (group_number,))

    @staticmethod
    def remove(
        target: XqyExpression | list[XqyExpression] | None,
        position: int | XqyExpression,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns a new sequence constructed from the value of $target with the item at
        the position specified by the value of $position removed.

        Parameters
        ----------
        target : XqyExpression | list[XqyExpression] | None
            The sequence of items from which items will be removed.
        position : int | XqyExpression
            The position in the target sequence from which the items will be removed.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:remove``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:remove
        """
        return FunctionCall("fn:remove", (target, position))

    @staticmethod
    def replace(
        input: str | XqyExpression | None,
        pattern: str | XqyExpression,
        replacement: str | XqyExpression,
        *,
        flags: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns a string constructed by replacing the specified $pattern on the $input
        string with the specified $replacement string.

        Parameters
        ----------
        input : str | XqyExpression | None
            The string to start with.
        pattern : str | XqyExpression
            The regular expression pattern to match. If the pattern does not match the
            $input string, the function will return the $input string unchanged.
        replacement : str | XqyExpression
            The regular expression pattern to replace the $pattern with. It can also be
            a capture expression (for more details, see http://www.w3.org/TR/xpath-
            functions/#func-replace ).
        flags : str | XqyExpression | None
            The flag representing how to interpret the regular expression. One of "s",
            "m", "i", or "x", as defined in http://www.w3.org/TR/xpath-functions/#flags
            .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:replace``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:replace
        """
        return _optional_call("fn:replace", input, pattern, replacement, flags)

    @staticmethod
    def resolve_qname(
        qname: str | XqyExpression | None,
        element: XqyExpression,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:QName value (that is, an expanded QName) by taking an xs:string
        that has the lexical form of an xs:QName (a string in the form "prefix:local-
        name" or "local-name") and resolving it using the in-scope namespaces for a
        given element.

        Parameters
        ----------
        qname : str | XqyExpression | None
            A string of the form "prefix:local-name".
        element : XqyExpression
            An element providing the in-scope namespaces to use to resolve the qualified
            name.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:resolve-QName``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:resolve-QName
        """
        return FunctionCall("fn:resolve-QName", (qname, element))

    @staticmethod
    def resolve_uri(
        relative: str | XqyExpression | None,
        *,
        base: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Resolves a relative URI against an absolute URI.

        Parameters
        ----------
        relative : str | XqyExpression | None
            A URI reference to resolve against the base.
        base : str | XqyExpression | None
            An absolute URI to use as the base of the resolution.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:resolve-uri``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:resolve-uri
        """
        return _optional_call("fn:resolve-uri", relative, base)

    @staticmethod
    def reverse(target: XqyExpression | list[XqyExpression] | None) -> FunctionCall:
        """Build a native XQuery expression.

        Reverses the order of items in a sequence.

        Parameters
        ----------
        target : XqyExpression | list[XqyExpression] | None
            The sequence of items to be reversed.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:reverse``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:reverse
        """
        return FunctionCall("fn:reverse", (target,))

    @staticmethod
    def root(arg: XqyExpression | None = UNSET) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the root of the tree to which $arg belongs.

        Parameters
        ----------
        arg : XqyExpression | None
            The node whose root node will be returned.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:root``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:root
        """
        return _optional_call("fn:root", arg)

    @staticmethod
    def round(arg: float | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the number with no fractional part that is closest to the argument.

        Parameters
        ----------
        arg : float | XqyExpression | None
            A numeric value to round.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:round``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:round
        """
        return FunctionCall("fn:round", (arg,))

    @staticmethod
    def round_half_to_even(
        arg: float | XqyExpression | None,
        *,
        precision: int | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        The value returned is the nearest (that is, numerically closest) numeric to $arg
        that is a multiple of ten to the power of minus $precision.

        Parameters
        ----------
        arg : float | XqyExpression | None
            A numeric value to round.
        precision : int | XqyExpression | None
            The precision to which to round the value.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:round-half-to-even``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:round-half-to-even
        """
        return _optional_call("fn:round-half-to-even", arg, precision)

    @staticmethod
    def seconds_from_date_time(
        arg: datetime.datetime | XqyExpression | None,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:decimal value between 0 and 60.999..., both inclusive representing
        the seconds and fractional seconds in the localized value of $arg.

        Parameters
        ----------
        arg : datetime.datetime | XqyExpression | None
            The dateTime whose seconds component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:seconds-from-dateTime``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:seconds-from-dateTime
        """
        return FunctionCall("fn:seconds-from-dateTime", (arg,))

    @staticmethod
    def seconds_from_duration(arg: str | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:decimal representing the seconds component in the canonical
        lexical representation of the value of $arg.

        Parameters
        ----------
        arg : str | XqyExpression | None
            The duration whose minute component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:seconds-from-duration``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:seconds-from-duration
        """
        return FunctionCall("fn:seconds-from-duration", (arg,))

    @staticmethod
    def seconds_from_time(arg: datetime.time | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:decimal value between 0 and 60.999..., both inclusive,
        representing the seconds and fractional seconds in the localized value of $arg.

        Parameters
        ----------
        arg : datetime.time | XqyExpression | None
            The time whose seconds component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:seconds-from-time``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:seconds-from-time
        """
        return FunctionCall("fn:seconds-from-time", (arg,))

    @staticmethod
    def starts_with(
        parameter1: str | XqyExpression | None,
        parameter2: str | XqyExpression | None,
        *,
        collation: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns true if the first parameter starts with the string from the second
        parameter, otherwise returns false.

        Parameters
        ----------
        parameter1 : str | XqyExpression | None
            The string from which to test.
        parameter2 : str | XqyExpression | None
            The string to test whether it is at the beginning of the first parameter.
        collation : str | XqyExpression | None
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:starts-with``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:starts-with
        """
        return _optional_call("fn:starts-with", parameter1, parameter2, collation)

    @staticmethod
    def static_base_uri() -> FunctionCall:
        """Build a native XQuery expression.

        Returns the value of the base-uri property from the static context.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:static-base-uri``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:static-base-uri
        """
        return FunctionCall("fn:static-base-uri")

    @staticmethod
    def string(arg: XqyExpression | None = UNSET) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the value of $arg represented as an xs:string.

        Parameters
        ----------
        arg : XqyExpression | None
            The item to be rendered as a string.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:string``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:string
        """
        return _optional_call("fn:string", arg)

    @staticmethod
    def string_join(
        parameter1: str | list[str] | XqyExpression | list[XqyExpression] | None,
        parameter2: str | XqyExpression,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:string created by concatenating the members of the $parameter1
        sequence using $parameter2 as a separator.

        Parameters
        ----------
        parameter1 : str | list[str] | XqyExpression | list[XqyExpression] | None
            A sequence of strings.
        parameter2 : str | XqyExpression
            A separator string to concatenate between the items in $parameter1.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:string-join``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:string-join
        """
        return FunctionCall("fn:string-join", (parameter1, parameter2))

    @staticmethod
    def string_length(
        source_string: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an integer representing the length of the specified string.

        Parameters
        ----------
        source_string : str | XqyExpression | None
            The string to calculate the length.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:string-length``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:string-length
        """
        return _optional_call("fn:string-length", source_string)

    @staticmethod
    def string_pad(
        pad_string: str | XqyExpression | None,
        pad_count: int | XqyExpression,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        [0.9-ml only] Returns a string representing the $padString concatenated with
        itself the number of times specified in $padCount.

        Parameters
        ----------
        pad_string : str | XqyExpression | None
            The string to pad.
        pad_count : int | XqyExpression
            The number of times to pad the string.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:string-pad``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:string-pad
        """
        return FunctionCall("fn:string-pad", (pad_string, pad_count))

    @staticmethod
    def string_to_codepoints(arg: str | XqyExpression) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the sequence of Unicode code points that constitute an xs:string.

        Parameters
        ----------
        arg : str | XqyExpression
            A string.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:string-to-codepoints``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:string-to-codepoints
        """
        return FunctionCall("fn:string-to-codepoints", (arg,))

    @staticmethod
    def subsequence(
        source_seq: XqyExpression | list[XqyExpression] | None,
        starting_loc: float | XqyExpression,
        *,
        length: float | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the contiguous sequence of items in the value of $sourceSeq beginning at
        the position indicated by the value of $startingLoc and continuing for the
        number of items indicated by the value of $length.

        Parameters
        ----------
        source_seq : XqyExpression | list[XqyExpression] | None
            The sequence of items from which a subsequence will be selected.
        starting_loc : float | XqyExpression
            The starting position of the start of the subsequence.
        length : float | XqyExpression | None
            The length of the subsequence.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:subsequence``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:subsequence
        """
        return _optional_call("fn:subsequence", source_seq, starting_loc, length)

    @staticmethod
    def substring(
        source_string: str | XqyExpression | None,
        starting_loc: float | XqyExpression,
        *,
        length: float | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns a substring starting from the $startingLoc and continuing for $length
        characters.

        Parameters
        ----------
        source_string : str | XqyExpression | None
            The string from which to create a substring.
        starting_loc : float | XqyExpression
            The number of characters from the start of the $sourceString.
        length : float | XqyExpression | None
            The number of characters beyond the $startingLoc.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:substring``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:substring
        """
        return _optional_call("fn:substring", source_string, starting_loc, length)

    @staticmethod
    def substring_after(
        input: str | XqyExpression | None,
        after: str | XqyExpression | None,
        *,
        collation: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the substring created by taking all of the input characters that occur
        after the specified $after characters.

        Parameters
        ----------
        input : str | XqyExpression | None
            The string from which to create the substring.
        after : str | XqyExpression | None
            The string after which the substring is created.
        collation : str | XqyExpression | None
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:substring-after``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:substring-after
        """
        return _optional_call("fn:substring-after", input, after, collation)

    @staticmethod
    def substring_before(
        input: str | XqyExpression | None,
        before: str | XqyExpression | None,
        *,
        collation: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the substring created by taking all of the input characters that occur
        before the specified $before characters.

        Parameters
        ----------
        input : str | XqyExpression | None
            The string from which to create the substring.
        before : str | XqyExpression | None
            The string before which the substring is created.
        collation : str | XqyExpression | None
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:substring-before``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:substring-before
        """
        return _optional_call("fn:substring-before", input, before, collation)

    @staticmethod
    def subtract_date_times_yielding_day_time_duration(
        srcval1: datetime.datetime | XqyExpression,
        srcval2: datetime.datetime | XqyExpression,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        [0.9-ml only, use the minus operator ( - ) instead] Returns the
        xdt:dayTimeDuration that corresponds to the difference between the normalized
        value of $srcval1 and the normalized value of $srcval2.

        Parameters
        ----------
        srcval1 : datetime.datetime | XqyExpression
            The second xs:dateTime value.
        srcval2 : datetime.datetime | XqyExpression
            The second xs:dateTime value.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:subtract-dateTimes-yielding-dayTimeDuration``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:subtract-dateTimes-yielding-dayTimeDuration
        """
        return FunctionCall(
            "fn:subtract-dateTimes-yielding-dayTimeDuration",
            (srcval1, srcval2),
        )

    @staticmethod
    def subtract_date_times_yielding_year_month_duration(
        srcval1: datetime.datetime | XqyExpression,
        srcval2: datetime.datetime | XqyExpression,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        [0.9-ml only, use the minus operator ( - ) instead] Returns the
        xdt:yearMonthDuration that corresponds to the difference between the normalized
        value of $srcval1 and the normalized value of $srcval2.

        Parameters
        ----------
        srcval1 : datetime.datetime | XqyExpression
            The second xs:dateTime value.
        srcval2 : datetime.datetime | XqyExpression
            The second xs:dateTime value.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:subtract-dateTimes-yielding-yearMonthDuration``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:subtract-dateTimes-yielding-yearMonthDuration
        """
        return FunctionCall(
            "fn:subtract-dateTimes-yielding-yearMonthDuration",
            (srcval1, srcval2),
        )

    @staticmethod
    def sum(
        arg: str
        | int
        | float
        | bool
        | list[str | int | float | bool]
        | XqyExpression
        | list[XqyExpression]
        | None,
        *,
        zero: str | int | float | bool | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns a value obtained by adding together the values in $arg.

        Parameters
        ----------
        arg : str | int | float | bool | list[str | int | float | bool] | XqyExpression | list[XqyExpression] | None
            The sequence of values to be summed.
        zero : str | int | float | bool | XqyExpression | None
            The value to return as zero if the input sequence is the empty sequence.
            This parameter is not available in the 0.9-ml XQuery dialect.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:sum``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:sum
        """
        return _optional_call("fn:sum", arg, zero)

    @staticmethod
    def system_property(property_name: str | XqyExpression) -> FunctionCall:
        """Build a native XQuery expression.

        Returns a string representing the value of the system property identified by the
        name.

        Parameters
        ----------
        property_name : str | XqyExpression
            The name of the property whose value is to be returned. Valid names are:
            xsl:version xsl:vendor xsl:vendor-url xsl:product-name xsl:product-version
            xsl:is-schema-aware xsl:supports-serialization xsl:supports-backwards-
            compatibility xsl:supports-namespace-axis

        Returns
        -------
        FunctionCall
            Composable call to ``fn:system-property``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:system-property
        """
        return FunctionCall("fn:system-property", (property_name,))

    @staticmethod
    def tail(seq: XqyExpression | list[XqyExpression] | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns all but the first item in a sequence.

        Parameters
        ----------
        seq : XqyExpression | list[XqyExpression] | None
            The function value.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:tail``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:tail
        """
        return FunctionCall("fn:tail", (seq,))

    @staticmethod
    def timezone_from_date(arg: datetime.date | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the timezone component of $arg if any.

        Parameters
        ----------
        arg : datetime.date | XqyExpression | None
            The date whose timezone component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:timezone-from-date``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:timezone-from-date
        """
        return FunctionCall("fn:timezone-from-date", (arg,))

    @staticmethod
    def timezone_from_date_time(
        arg: datetime.datetime | XqyExpression | None,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the timezone component of $arg if any.

        Parameters
        ----------
        arg : datetime.datetime | XqyExpression | None
            The dateTime whose timezone component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:timezone-from-dateTime``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:timezone-from-dateTime
        """
        return FunctionCall("fn:timezone-from-dateTime", (arg,))

    @staticmethod
    def timezone_from_time(arg: datetime.time | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the timezone component of $arg if any.

        Parameters
        ----------
        arg : datetime.time | XqyExpression | None
            The time whose timezone component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:timezone-from-time``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:timezone-from-time
        """
        return FunctionCall("fn:timezone-from-time", (arg,))

    @staticmethod
    def tokenize(
        input: str | XqyExpression | None,
        pattern: str | XqyExpression,
        *,
        flags: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns a sequence of strings constructed by breaking the specified input into
        substrings separated by the specified $pattern.

        Parameters
        ----------
        input : str | XqyExpression | None
            The string to tokenize.
        pattern : str | XqyExpression
            The regular expression pattern from which to separate the tokens.
        flags : str | XqyExpression | None
            The flag representing how to interpret the regular expression. One of "s",
            "m", "i", or "x", as defined in http://www.w3.org/TR/xpath-functions/#flags
            .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:tokenize``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:tokenize
        """
        return _optional_call("fn:tokenize", input, pattern, flags)

    @staticmethod
    def trace(
        value: XqyExpression | list[XqyExpression] | None,
        label: str | XqyExpression,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Return the input $value unchanged and, if $label is the name of an enabled
        server event, log event to the App Server log file
        <install_dir>/Logs/<port>_ErrorLog.txt; where <install_dir> is the MarkLogic
        install directory, and <port> is the port number of the current App Server or
        "TaskServer" if the current request is running on the Task Server.

        Parameters
        ----------
        value : XqyExpression | list[XqyExpression] | None
            The values to trace.
        label : str | XqyExpression
            A string label for the trace output.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:trace``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:trace
        """
        return FunctionCall("fn:trace", (value, label))

    @staticmethod
    def translate(
        src: str | XqyExpression | None,
        map_string: str | XqyExpression | None,
        trans_string: str | XqyExpression | None,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns a string where every character in $src that occurs in some position in
        the $mapString is translated into the $transString character in the
        corresponding location of the $mapString character.

        Parameters
        ----------
        src : str | XqyExpression | None
            The string to translate characters.
        map_string : str | XqyExpression | None
            The string representing characters to be translated.
        trans_string : str | XqyExpression | None
            The string representing the characters to which the $mapString characters
            are translated.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:translate``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:translate
        """
        return FunctionCall("fn:translate", (src, map_string, trans_string))

    @staticmethod
    def true() -> FunctionCall:
        """Build a native XQuery expression.

        Returns the xs:boolean value true.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:true``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:true
        """
        return FunctionCall("fn:true")

    @staticmethod
    def type_available(type_name: str | XqyExpression) -> FunctionCall:
        """Build a native XQuery expression.

        Returns true if and only if there is a type whose name matches the value of the
        $type-name argument is present in the static context.

        Parameters
        ----------
        type_name : str | XqyExpression
            The $type-name is a string containing a lexical QName. It may be a name of a
            builtin-type, type imported using xsl:import-schema, or an extension type.
            This parameter is mandatory. The lexical QName is expanded using the
            namespace declarations in scope for the expression. If the lexical QName is
            unprefixed, then the default namespace is used in the expanded QName.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:type-available``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:type-available
        """
        return FunctionCall("fn:type-available", (type_name,))

    @staticmethod
    def unordered(
        source_seq: XqyExpression | list[XqyExpression] | None,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the items of $sourceSeq in an implementation dependent order.

        Parameters
        ----------
        source_seq : XqyExpression | list[XqyExpression] | None
            The sequence of items.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:unordered``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:unordered
        """
        return FunctionCall("fn:unordered", (source_seq,))

    @staticmethod
    def unparsed_entity_public_id(entity_name: str | XqyExpression) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the public identifier of the unparsed entity specified by the $entity-
        name parameter.

        Parameters
        ----------
        entity_name : str | XqyExpression
            The entity name.
            ---

        Returns
        -------
        FunctionCall
            Composable call to ``fn:unparsed-entity-public-id``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:unparsed-entity-public-id
        """
        return FunctionCall("fn:unparsed-entity-public-id", (entity_name,))

    @staticmethod
    def unparsed_entity_uri(entity_name: str | XqyExpression) -> FunctionCall:
        """Build a native XQuery expression.

        Always returns the zero length string.

        Parameters
        ----------
        entity_name : str | XqyExpression
            The entity name.
            ---

        Returns
        -------
        FunctionCall
            Composable call to ``fn:unparsed-entity-uri``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:unparsed-entity-uri
        """
        return FunctionCall("fn:unparsed-entity-uri", (entity_name,))

    @staticmethod
    def unparsed_text(
        href: str | XqyExpression,
        *,
        encoding: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Reads a file stored in the database as either text or binary file and returns
        its contents as a string.

        Parameters
        ----------
        href : str | XqyExpression
            The $href is a string containing a URI reference. It must identify a
            resource that can be read as text. If the URI is a relative URI then it is
            resolved relative to the base URI from the static context.
        encoding : str | XqyExpression | None
            If $encoding parameter is present and the URI points to a "text" file, the
            encoding is ignored since all the files are in UTF-8 in the database.
            However, if the URI points to a binary file, then an attempt is made to
            convert it from the specified encoding and the string value of the results
            of the conversion is returned. If the conversion fails, an exception is
            returned. The $encoding parameter must be passed when the URI resolves to a
            binary resource. An automatic encoding detector will be used if the value
            auto is specified. If $encoding is not present, the encoding defaults to
            UTF-8.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:unparsed-text``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:unparsed-text
        """
        return _optional_call("fn:unparsed-text", href, encoding)

    @staticmethod
    def unparsed_text_available(
        href: str | XqyExpression,
        *,
        encoding: str | XqyExpression | None = UNSET,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns true if a call to unparsed-text would succeed with identical arguments.

        Parameters
        ----------
        href : str | XqyExpression
            The $href is a string containing a URI reference. It must identify a
            resource that can be read as text. If the URI is a relative URI then it is
            resolved relative to the base URI from the static context.
        encoding : str | XqyExpression | None
            If $encoding parameter is present and the URI points to a "text" file, the
            encoding is ignored since all the files are in UTF-8 in the database.
            However, if the URI points to a binary file, then an attempt will be made to
            convert it to the specified encoding and if the conversion succeeds it
            returns true. If the conversion fails, an exception is returned. The
            $encoding parameter must be passed when the URI resolves to a binary
            resource.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        FunctionCall
            Composable call to ``fn:unparsed-text-available``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:unparsed-text-available
        """
        return _optional_call("fn:unparsed-text-available", href, encoding)

    @staticmethod
    def upper_case(string: str | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns the specified string converting all of the characters to upper-case
        characters.

        Parameters
        ----------
        string : str | XqyExpression | None
            The string to upper-case.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:upper-case``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:upper-case
        """
        return FunctionCall("fn:upper-case", (string,))

    @staticmethod
    def year_from_date(arg: datetime.date | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:integer representing the year component in the localized value of
        $arg.

        Parameters
        ----------
        arg : datetime.date | XqyExpression | None
            The date whose year component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:year-from-date``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:year-from-date
        """
        return FunctionCall("fn:year-from-date", (arg,))

    @staticmethod
    def year_from_date_time(
        arg: datetime.datetime | XqyExpression | None,
    ) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:integer representing the year component in the localized value of
        $arg.

        Parameters
        ----------
        arg : datetime.datetime | XqyExpression | None
            The dateTime whose year component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:year-from-dateTime``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:year-from-dateTime
        """
        return FunctionCall("fn:year-from-dateTime", (arg,))

    @staticmethod
    def years_from_duration(arg: str | XqyExpression | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns an xs:integer representing the years component in the canonical lexical
        representation of the value of $arg.

        Parameters
        ----------
        arg : str | XqyExpression | None
            The duration whose year component will be returned.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:years-from-duration``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:years-from-duration
        """
        return FunctionCall("fn:years-from-duration", (arg,))

    @staticmethod
    def zero_or_one(arg: XqyExpression | list[XqyExpression] | None) -> FunctionCall:
        """Build a native XQuery expression.

        Returns $arg if it contains zero or one items.

        Parameters
        ----------
        arg : XqyExpression | list[XqyExpression] | None
            The sequence of items.

        Returns
        -------
        FunctionCall
            Composable call to ``fn:zero-or-one``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:zero-or-one
        """
        return FunctionCall("fn:zero-or-one", (arg,))
