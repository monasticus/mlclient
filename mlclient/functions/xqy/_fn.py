"""Native fn: expression builders for XQuery composition.

Arguments are data or Expr trees. None passes the empty sequence; omitted
optional arguments retain the native function's context-dependent defaults.
XSLT-only and legacy functions retain their native context/dialect restrictions.
"""

from __future__ import annotations

from mlclient._experimental import experimental
from mlclient._options import UNSET
from mlclient.functions.xqy._expr import Expr, _FunctionCall


def _optional_call(name: str, *arguments) -> Expr:
    """Trim omitted trailing arguments; preserve explicit empty sequences.

    Parameters
    ----------
    name : str
        Native function name.
    arguments : object
        Native positional arguments; UNSET marks an omitted optional slot.

    Returns
    -------
    Expr
        Call with interior omissions represented by empty sequences.
    """
    end = len(arguments)
    while end and arguments[end - 1] is UNSET:
        end -= 1
    return _FunctionCall(
        name,
        tuple(None if arg is UNSET else arg for arg in arguments[:end]),
    )


@experimental()
class Fn:
    """Pure fn: builders; native context and dialect requirements still apply."""

    @staticmethod
    def abs(arg) -> Expr:
        """Build a native XQuery expression.

        Returns the absolute value of $arg.

        Parameters
        ----------
        arg : numeric?
            A numeric value.

        Returns
        -------
        Expr
            Composable call to ``fn:abs``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:abs
        """
        return _FunctionCall("fn:abs", (arg,))

    @staticmethod
    def adjust_date_to_timezone(arg, *, timezone=UNSET) -> Expr:
        """Build a native XQuery expression.

        Adjusts an xs:date value to a specific timezone, or to no timezone at all.

        Parameters
        ----------
        arg : xs:date?
            The date to adjust to the new timezone.
        timezone : xs:dayTimeDuration?
            The new timezone for the date.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:adjust-date-to-timezone``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:adjust-date-to-timezone
        """
        return _optional_call("fn:adjust-date-to-timezone", arg, timezone)

    @staticmethod
    def adjust_date_time_to_timezone(arg, *, timezone=UNSET) -> Expr:
        """Build a native XQuery expression.

        Adjusts an xs:dateTime value to a specific timezone, or to no timezone at all.

        Parameters
        ----------
        arg : xs:dateTime?
            The dateTime to adjust to the new timezone.
        timezone : xs:dayTimeDuration?
            The new timezone for the dateTime.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:adjust-dateTime-to-timezone``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:adjust-dateTime-to-timezone
        """
        return _optional_call("fn:adjust-dateTime-to-timezone", arg, timezone)

    @staticmethod
    def adjust_time_to_timezone(arg, *, timezone=UNSET) -> Expr:
        """Build a native XQuery expression.

        Adjusts an xs:time value to a specific timezone, or to no timezone at all.

        Parameters
        ----------
        arg : xs:time?
            The time to adjust to the new timezone.
        timezone : xs:dayTimeDuration?
            The new timezone for the date.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:adjust-time-to-timezone``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:adjust-time-to-timezone
        """
        return _optional_call("fn:adjust-time-to-timezone", arg, timezone)

    @staticmethod
    def analyze_string(in_, regex, *, flags=UNSET) -> Expr:
        """Build a native XQuery expression.

        The result of the function is a new element node whose string value is the
        original string, but which contains markup to show which parts of the input
        match the regular expression.

        Parameters
        ----------
        in_ : xs:string?
            The string to start with.
        regex : xs:string
            The regular expression pattern to match.
        flags : xs:string
            The flag representing how to interpret the regular expression. One of "s",
            "m", "i", or "x", as defined in http://www.w3.org/TR/xpath-functions/#flags
            .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:analyze-string``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:analyze-string
        """
        return _optional_call("fn:analyze-string", in_, regex, flags)

    @staticmethod
    def avg(arg) -> Expr:
        """Build a native XQuery expression.

        Returns the average of the values in the input sequence $arg, that is, the sum
        of the values divided by the number of values.

        Parameters
        ----------
        arg : xs:anyAtomicType*
            The sequence of values to average.

        Returns
        -------
        Expr
            Composable call to ``fn:avg``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:avg
        """
        return _FunctionCall("fn:avg", (arg,))

    @staticmethod
    def base_uri(arg=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns the value of the base-uri property for the specified node.

        Parameters
        ----------
        arg : node()?
            The node whose base-uri is to be returned.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:base-uri``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:base-uri
        """
        return _optional_call("fn:base-uri", arg)

    @staticmethod
    def boolean(arg, *, collation=UNSET) -> Expr:
        """Build a native XQuery expression.

        Computes the effective boolean value of the sequence $arg.

        Parameters
        ----------
        arg : item()*
            A sequence of items.
        collation : xs:string
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:boolean``.

        Notes
        -----
        When using XQuery version "1.0-ml", this function implements the semantics from
        May 2003.
        If $arg is the empty sequence, fn:boolean returns false.
        If $arg is a sequence whose first item is a node, fn:boolean returns true.
        If $arg is a singleton value of type xs:boolean or a derived from xs:boolean,
        fn:boolean returns $arg .
        If $arg is a singleton value of type xs:string or a type derived from xs:string
        or xs:untypedAtomic, fn:boolean returns false if the operand value has zero
        length; otherwise it returns true.
        If $arg is a singleton value of any numeric type or a type derived from a
        numeric type, fn:boolean returns false if the operand value is NaN or is
        numerically equal to zero; otherwise it returns true.
        In all other cases, fn:boolean raises a type error [err:FORG0006] when run in
        XQuery strict mode (1.0).
        The static semantics of this function are described in Section 7.2.4 The
        fn:boolean function[FS] .
        Note:
        The result of this function is not necessarily the same as " $arg cast as
        xs:boolean ". For example, fn:boolean("false") returns the value "true" whereas
        "false" cast as xs:boolean returns false.

        Native reference: https://docs.marklogic.com/fn:boolean
        """
        return _optional_call("fn:boolean", arg, collation)

    @staticmethod
    def ceiling(arg) -> Expr:
        """Build a native XQuery expression.

        Returns the smallest (closest to negative infinity) number with no fractional
        part that is not less than the value of $arg.

        Parameters
        ----------
        arg : numeric?
            A numeric value.

        Returns
        -------
        Expr
            Composable call to ``fn:ceiling``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:ceiling
        """
        return _FunctionCall("fn:ceiling", (arg,))

    @staticmethod
    def codepoint_equal(comparand1, comparand2) -> Expr:
        """Build a native XQuery expression.

        Returns true if the specified parameters are the same Unicode code point,
        otherwise returns false.

        Parameters
        ----------
        comparand1 : xs:string?
            A string to be compared.
        comparand2 : xs:string?
            A string to be compared.

        Returns
        -------
        Expr
            Composable call to ``fn:codepoint-equal``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:codepoint-equal
        """
        return _FunctionCall("fn:codepoint-equal", (comparand1, comparand2))

    @staticmethod
    def codepoints_to_string(arg) -> Expr:
        """Build a native XQuery expression.

        Creates an xs:string from a sequence of Unicode code points.

        Parameters
        ----------
        arg : xs:integer*
            A sequence of Unicode code points.

        Returns
        -------
        Expr
            Composable call to ``fn:codepoints-to-string``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:codepoints-to-string
        """
        return _FunctionCall("fn:codepoints-to-string", (arg,))

    @staticmethod
    def collection(uri=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns all of the documents that belong to the specified collection(s).

        Parameters
        ----------
        uri : xs:string*
            The URI of the collection to retrieve. If you omit this parameter, returns
            all of the documents in the database. If you specify a list of URIs, returns
            all of the documents in all of the collections at the URIs specified in the
            list.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:collection``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:collection
        """
        return _optional_call("fn:collection", uri)

    @staticmethod
    def compare(comparand1, comparand2, *, collation=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns -1, 0, or 1, depending on whether the value of the $comparand1 is
        respectively less than, equal to, or greater than the value of $comparand2,
        according to the rules of the collation that is used.

        Parameters
        ----------
        comparand1 : xs:string?
            A string to be compared.
        comparand2 : xs:string?
            A string to be compared.
        collation : xs:string
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:compare``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:compare
        """
        return _optional_call("fn:compare", comparand1, comparand2, collation)

    @staticmethod
    def concat(parameter1, *parameters) -> Expr:
        """Build a native XQuery expression.

        Returns the xs:string that is the concatenation of the values of the specified
        parameters.

        Parameters
        ----------
        parameter1 : xs:anyAtomicType?
            A value.
        parameters : xs:anyAtomicType?,...
            A value.

        Returns
        -------
        Expr
            Composable call to ``fn:concat``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:concat
        """
        return _FunctionCall("fn:concat", (parameter1, *parameters))

    @staticmethod
    def contains(parameter1, parameter2, *, collation=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns true if the first parameter contains the string from the second
        parameter, otherwise returns false.

        Parameters
        ----------
        parameter1 : xs:string?
            The string from which to test.
        parameter2 : xs:string?
            The string to test for existence in the first parameter.
        collation : xs:string
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:contains``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:contains
        """
        return _optional_call("fn:contains", parameter1, parameter2, collation)

    @staticmethod
    def count(sequence, *, maximum=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns the number of items in the value of $arg.

        Parameters
        ----------
        sequence : item()*
            The sequence of items to count.
        maximum : xs:double?
            The maximum value of the count to return. MarkLogic Server will stop count
            when the $maximum value is reached and return the $maximum value. This is an
            extension to the W3C standard fn:count function.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:count``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:count
        """
        return _optional_call("fn:count", sequence, maximum)

    @staticmethod
    def current() -> Expr:
        """Build a native XQuery expression.

        Returns the item that was the context item at the point where the expression was
        invoked from the XSLT stylesheet.

        Returns
        -------
        Expr
            Composable call to ``fn:current``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:current
        """
        return _FunctionCall("fn:current")

    @staticmethod
    def current_date() -> Expr:
        """Build a native XQuery expression.

        Returns xs:date(fn:current-dateTime()).

        Returns
        -------
        Expr
            Composable call to ``fn:current-date``.

        Notes
        -----
        fn:current-date()
        xs:date
        fn:current-date()
        2004-05-12+01:00

        Native reference: https://docs.marklogic.com/fn:current-date
        """
        return _FunctionCall("fn:current-date")

    @staticmethod
    def current_date_time() -> Expr:
        """Build a native XQuery expression.

        Returns the current dateTime value (with timezone) from the dynamic context.

        Returns
        -------
        Expr
            Composable call to ``fn:current-dateTime``.

        Notes
        -----
        fn:current-dateTime()
        xs:dateTime
        fn:current-dateTime()
        2004-05-12T18:17:15.125Z

        Native reference: https://docs.marklogic.com/fn:current-dateTime
        """
        return _FunctionCall("fn:current-dateTime")

    @staticmethod
    def current_group() -> Expr:
        """Build a native XQuery expression.

        Returns the current regex group.

        Returns
        -------
        Expr
            Composable call to ``fn:current-group``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:current-group
        """
        return _FunctionCall("fn:current-group")

    @staticmethod
    def current_grouping_key() -> Expr:
        """Build a native XQuery expression.

        Returns the current regex grouping key.

        Returns
        -------
        Expr
            Composable call to ``fn:current-grouping-key``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:current-grouping-key
        """
        return _FunctionCall("fn:current-grouping-key")

    @staticmethod
    def current_time() -> Expr:
        """Build a native XQuery expression.

        Returns xs:time(fn:current-dateTime()).

        Returns
        -------
        Expr
            Composable call to ``fn:current-time``.

        Notes
        -----
        fn:current-time()
        xs:time
        fn:current-time()
        23:17:00.000-05:00

        Native reference: https://docs.marklogic.com/fn:current-time
        """
        return _FunctionCall("fn:current-time")

    @staticmethod
    def data(arg) -> Expr:
        """Build a native XQuery expression.

        Takes a sequence of items and returns a sequence of atomic values.

        Parameters
        ----------
        arg : item()*
            The items whose typed values are to be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:data``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:data
        """
        return _FunctionCall("fn:data", (arg,))

    @staticmethod
    def date_time(arg1, arg2) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:dateTime value created by combining an xs:date and an xs:time.

        Parameters
        ----------
        arg1 : xs:date
            The date to be combined with the time argument.
        arg2 : xs:time
            The time to be combined with the date argument.

        Returns
        -------
        Expr
            Composable call to ``fn:dateTime``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:dateTime
        """
        return _FunctionCall("fn:dateTime", (arg1, arg2))

    @staticmethod
    def day_from_date(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:integer between 1 and 31, both inclusive, representing the day
        component in the localized value of $arg.

        Parameters
        ----------
        arg : xs:date?
            The date whose day component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:day-from-date``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:day-from-date
        """
        return _FunctionCall("fn:day-from-date", (arg,))

    @staticmethod
    def day_from_date_time(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:integer between 1 and 31, both inclusive, representing the day
        component in the localized value of $arg.

        Parameters
        ----------
        arg : xs:dateTime?
            The dateTime whose day component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:day-from-dateTime``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:day-from-dateTime
        """
        return _FunctionCall("fn:day-from-dateTime", (arg,))

    @staticmethod
    def days_from_duration(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:integer representing the days component in the canonical lexical
        representation of the value of $arg.

        Parameters
        ----------
        arg : xs:duration?
            The duration whose day component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:days-from-duration``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:days-from-duration
        """
        return _FunctionCall("fn:days-from-duration", (arg,))

    @staticmethod
    def deep_equal(parameter1, parameter2, *, collation=UNSET) -> Expr:
        """Build a native XQuery expression.

        This function assesses whether two sequences are deep-equal to each other.

        Parameters
        ----------
        parameter1 : item()*
            The first sequence of items, each item should be an atomic value or node.
        parameter2 : item()*
            The sequence of items to compare to the first sequence of items, again each
            item should be an atomic value or node.
        collation : xs:string
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:deep-equal``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:deep-equal
        """
        return _optional_call("fn:deep-equal", parameter1, parameter2, collation)

    @staticmethod
    def default_collation() -> Expr:
        """Build a native XQuery expression.

        Returns the value of the default collation property from the static context.

        Returns
        -------
        Expr
            Composable call to ``fn:default-collation``.

        Notes
        -----
        Developer's Guide

        Native reference: https://docs.marklogic.com/fn:default-collation
        """
        return _FunctionCall("fn:default-collation")

    @staticmethod
    def distinct_nodes(nodes) -> Expr:
        """Build a native XQuery expression.

        [0.9-ml only] Returns the sequence resulting from removing from the input
        sequence all but one of a set of nodes that have the same identity as one
        another.

        Parameters
        ----------
        nodes : node()*
            A sequence of nodes from which to eliminate duplicate nodes (nodes with the
            same identity) so that only one node of each identity remains.

        Returns
        -------
        Expr
            Composable call to ``fn:distinct-nodes``.

        Notes
        -----
        Note that for a node to have the same identity as another node, it must be
        exactly the same node (not an equivalent node). For example, for a node bound to
        the variable $x to have the same identity as a node bound to the variable $y,
        the following must return true:
        $x is $y

        Native reference: https://docs.marklogic.com/fn:distinct-nodes
        """
        return _FunctionCall("fn:distinct-nodes", (nodes,))

    @staticmethod
    def distinct_values(arg, *, collation=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns the sequence that results from removing from $arg all but one of a set
        of values that are eq to one other.

        Parameters
        ----------
        arg : item()*
            A sequence of items.
        collation : xs:string
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:distinct-values``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:distinct-values
        """
        return _optional_call("fn:distinct-values", arg, collation)

    @staticmethod
    def doc(uri=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns the document(s) stored in the database at the specified URI(s).

        Parameters
        ----------
        uri : xs:string*
            The URI of the document to retrieve. If you omit this parameter, returns all
            of the documents in the database - this is only allowed if you're not using
            xquery version 1.0 strict. If you specify a list of URIs, returns all of the
            documents at the URIs specified in the list.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:doc``.

        Notes
        -----
        document-node()
        element()
        text()
        object-node()
        array-node()
        binary()

        Native reference: https://docs.marklogic.com/fn:doc
        """
        return _optional_call("fn:doc", uri)

    @staticmethod
    def doc_available(uri) -> Expr:
        """Build a native XQuery expression.

        If fn:doc($uri) returns a document node, this function returns true.

        Parameters
        ----------
        uri : xs:string?
            The URI of the document to check.

        Returns
        -------
        Expr
            Composable call to ``fn:doc-available``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:doc-available
        """
        return _FunctionCall("fn:doc-available", (uri,))

    @staticmethod
    def document(uris, *, base_node=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns the document(s) stored in the database at the specified URI(s).

        Parameters
        ----------
        uris : item()*
            The $uris is a sequence of the URI(s) of the document(s) to be retrieved.
            This parameter is mandatory. However you may pass a singleton sequence with
            an empty string in it. In that case it will return the stylesheet that
            contains this function call when called from XSLT stylesheet and all the
            documents in the database when called from XQuery- this is allowed only when
            you are not using version 1.0 strict. If any URI in this sequence is an
            absolute URI, then it is used as is. If it is a relative URI, it is resolved
            against a base URI specified in the second argument.
        base_node : node()
            If $base-node is supplied, its base URI is used to resolve relative URIs in
            uri-sequence. If it is not supplied, the base URI of the node that contained
            the fn:document() call is used.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:document``.

        Notes
        -----
        If no second argument is specified, the URI resolves using the base-uri of the
        calling module. This can cause surprising results if the URI you are resolving
        is not rooted but the module from which you call it has a base-uri. When calling
        fn:document from an xdmp:eval , the calling module is defined to have no base-
        uri. When calling from an XQuery module or an XSLT stylesheet, the base-uri is
        the URI of the module or stylesheet. For an example to demonstrate this , see
        the second example below.
        For the URI to be exactly what you enter, use fn:doc instead.

        Native reference: https://docs.marklogic.com/fn:document
        """
        return _optional_call("fn:document", uris, base_node)

    @staticmethod
    def document_uri(arg) -> Expr:
        """Build a native XQuery expression.

        Returns the value of the document-uri property for the specified node.

        Parameters
        ----------
        arg : node()?
            The node whose document-uri is to be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:document-uri``.

        Notes
        -----
        fn:document-uri
        fn:base-uri
        xdmp:node-uri

        Native reference: https://docs.marklogic.com/fn:document-uri
        """
        return _FunctionCall("fn:document-uri", (arg,))

    @staticmethod
    def element_available(element_name) -> Expr:
        """Build a native XQuery expression.

        Returns true if and only if the name of an XSLT instruction is passed in.

        Parameters
        ----------
        element_name : xs:string
            The name of the element to test.

        Returns
        -------
        Expr
            Composable call to ``fn:element-available``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:element-available
        """
        return _FunctionCall("fn:element-available", (element_name,))

    @staticmethod
    def empty(sequence) -> Expr:
        """Build a native XQuery expression.

        If the value of $arg is the empty sequence, the function returns true;
        otherwise, the function returns false.

        Parameters
        ----------
        sequence : item()*
            A sequence to test.

        Returns
        -------
        Expr
            Composable call to ``fn:empty``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:empty
        """
        return _FunctionCall("fn:empty", (sequence,))

    @staticmethod
    def encode_for_uri(uri_part) -> Expr:
        """Build a native XQuery expression.

        Invertible function that escapes characters required to be escaped inside path
        segments of URIs.

        Parameters
        ----------
        uri_part : xs:string
            A string representing an unescaped URI.

        Returns
        -------
        Expr
            Composable call to ``fn:encode-for-uri``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:encode-for-uri
        """
        return _FunctionCall("fn:encode-for-uri", (uri_part,))

    @staticmethod
    def ends_with(parameter1, parameter2, *, collation=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns true if the first parameter ends with the string from the second
        parameter, otherwise returns false.

        Parameters
        ----------
        parameter1 : xs:string?
            The parameter from which to test.
        parameter2 : xs:string?
            The string to test whether it is at the end of the first parameter.
        collation : xs:string
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:ends-with``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:ends-with
        """
        return _optional_call("fn:ends-with", parameter1, parameter2, collation)

    @staticmethod
    def error(error=UNSET, description=UNSET, data=UNSET) -> Expr:
        """Build a native XQuery expression.

        [1.0 and 1.0-ml only, 0.9-ml has a different signature] Throw the given error.

        Parameters
        ----------
        error : xs:QName?
            Error code, as an xs:QName . Note that this parameter does not exist in
            0.9-ml.
            Omit to use the native default; None explicitly passes ().
        description : xs:string
            String description to be printed with the error.
            Omit to use the native default; None explicitly passes ().
        data : item()*
            Parameters to the error message.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:error``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:error
        """
        return _optional_call("fn:error", error, description, data)

    @staticmethod
    def escape_html_uri(uri_part) -> Expr:
        """Build a native XQuery expression.

        %-escapes everything except printable ASCII characters.

        Parameters
        ----------
        uri_part : xs:string
            A string representing an unescaped URI.

        Returns
        -------
        Expr
            Composable call to ``fn:escape-html-uri``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:escape-html-uri
        """
        return _FunctionCall("fn:escape-html-uri", (uri_part,))

    @staticmethod
    def escape_uri(uri_part, escape_reserved) -> Expr:
        """Build a native XQuery expression.

        This is a May 2003 function, and is only available in compatibility mode (XQuery
        0.9-ML)--it has been replaced with fn:encode-for-uri, fn:iri-to-uri, and
        fn:escape-html-uri.

        Parameters
        ----------
        uri_part : xs:string
            A string representing an unescaped URI.
        escape_reserved : xs:boolean
            Specify a boolean value of true to return an escaped URI or a boolean value
            of false to return an unescaped URI.

        Returns
        -------
        Expr
            Composable call to ``fn:escape-uri``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:escape-uri
        """
        return _FunctionCall("fn:escape-uri", (uri_part, escape_reserved))

    @staticmethod
    def exactly_one(arg) -> Expr:
        """Build a native XQuery expression.

        Returns $arg if it contains exactly one item.

        Parameters
        ----------
        arg : item()*
            The sequence of items.

        Returns
        -------
        Expr
            Composable call to ``fn:exactly-one``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:exactly-one
        """
        return _FunctionCall("fn:exactly-one", (arg,))

    @staticmethod
    def exists(sequence) -> Expr:
        """Build a native XQuery expression.

        If the value of $arg is not the empty sequence, the function returns true;
        otherwise, the function returns false.

        Parameters
        ----------
        sequence : item()*
            A sequence to test.

        Returns
        -------
        Expr
            Composable call to ``fn:exists``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:exists
        """
        return _FunctionCall("fn:exists", (sequence,))

    @staticmethod
    def expanded_qname(param_uri, param_local) -> Expr:
        """Build a native XQuery expression.

        [0.9-ml only, use fn:QName instead] Returns an xs:QName with the namespace URI
        given in $paramURI and the local name in $paramLocal.

        Parameters
        ----------
        param_uri : xs:string?
            A namespace URI, as a string.
        param_local : xs:string
            A localname, as a string.

        Returns
        -------
        Expr
            Composable call to ``fn:expanded-QName``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:expanded-QName
        """
        return _FunctionCall("fn:expanded-QName", (param_uri, param_local))

    @staticmethod
    def false() -> Expr:
        """Build a native XQuery expression.

        Returns the xs:boolean value false.

        Returns
        -------
        Expr
            Composable call to ``fn:false``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:false
        """
        return _FunctionCall("fn:false")

    @staticmethod
    def filter(function, seq) -> Expr:
        """Build a native XQuery expression.

        Returns those items from the sequence $seq for which the supplied function
        $function returns true.

        Parameters
        ----------
        function : function(item()) as xs:boolean
            The function value.
        seq : item()*
            The function value.

        Returns
        -------
        Expr
            Composable call to ``fn:filter``.

        Notes
        -----
        Function arguments must be XQuery Expr values, not Python callables.
        Native reference: https://docs.marklogic.com/fn:filter
        """
        return _FunctionCall("fn:filter", (function, seq))

    @staticmethod
    def floor(arg) -> Expr:
        """Build a native XQuery expression.

        Returns the largest (closest to positive infinity) number with no fractional
        part that is not greater than the value of $arg.

        Parameters
        ----------
        arg : numeric?
            A numeric value.

        Returns
        -------
        Expr
            Composable call to ``fn:floor``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:floor
        """
        return _FunctionCall("fn:floor", (arg,))

    @staticmethod
    def fold_left(function, zero, seq) -> Expr:
        """Build a native XQuery expression.

        Processes the supplied sequence from left to right, applying the supplied
        function repeatedly to each item in turn, together with an accumulated result
        value.

        Parameters
        ----------
        function : function(item()*, item()) as item()*
            The fold function value.
        zero : item()*
            The zero argument.
        seq : item()*
            The sequence to fold

        Returns
        -------
        Expr
            Composable call to ``fn:fold-left``.

        Notes
        -----
        Function arguments must be XQuery Expr values, not Python callables.
        Native reference: https://docs.marklogic.com/fn:fold-left
        """
        return _FunctionCall("fn:fold-left", (function, zero, seq))

    @staticmethod
    def fold_right(function, zero, seq) -> Expr:
        """Build a native XQuery expression.

        Processes the supplied sequence from right to left, applying the supplied
        function repeatedly to each item in turn, together with an accumulated result
        value.

        Parameters
        ----------
        function : function(item(), item()*) as item()*
            The fold function value.
        zero : item()*
            The zero argument.
        seq : item()*
            The sequence to fold

        Returns
        -------
        Expr
            Composable call to ``fn:fold-right``.

        Notes
        -----
        Function arguments must be XQuery Expr values, not Python callables.
        Native reference: https://docs.marklogic.com/fn:fold-right
        """
        return _FunctionCall("fn:fold-right", (function, zero, seq))

    @staticmethod
    def format_date(
        value, picture, *, language=UNSET, calendar=UNSET, country=UNSET,
    ) -> Expr:
        """Build a native XQuery expression.

        Returns a formatted date value based on the picture argument.

        Parameters
        ----------
        value : xs:date
            The given date $value that needs to be formatted.
        picture : xs:string
            The desired string representation of the given date $value . The picture
            string is a sequence of characters, in which the characters represent
            variables such as, decimal-separator-sign, grouping-sign, zero-digit-sign,
            digit-sign, pattern-separator, percent sign and per-mille-sign. For details
            on the picture string, see http://www.w3.org/TR/xslt20/#date-picture-string
            .
        language : xs:string
            The desired language for string representation of the date $value .
            Omit to use the native default; None explicitly passes ().
        calendar : xs:string
            The only calendar supported at this point is "Gregorian" or "AD".
            Omit to use the native default; None explicitly passes ().
        country : xs:string
            $country is used the specification to take into account country specific
            string representation.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:format-date``.

        Notes
        -----
        Dates before October 15, 1582 (the start of the Gregorian calendar) will not
        return the correct date value.

        Native reference: https://docs.marklogic.com/fn:format-date
        """
        return _optional_call(
            "fn:format-date", value, picture, language, calendar, country,
        )

    @staticmethod
    def format_date_time(
        value, picture, *, language=UNSET, calendar=UNSET, country=UNSET,
    ) -> Expr:
        """Build a native XQuery expression.

        Returns a formatted dateTime value based on the picture argument.

        Parameters
        ----------
        value : xs:dateTime
            The given dateTime $value that needs to be formatted.
        picture : xs:string
            The desired string representation of the given dateTime $value . The picture
            string is a sequence of characters, in which the characters represent
            variables such as, decimal-separator-sign, grouping-sign, zero-digit-sign,
            digit-sign, pattern-separator, percent sign and per-mille-sign. For details
            on the picture string, see http://www.w3.org/TR/xslt20/#date-picture-string
            .
        language : xs:string
            The desired language for string representation of the dateTime $value .
            Omit to use the native default; None explicitly passes ().
        calendar : xs:string
            The only calendar supported at this point is "Gregorian" or "AD".
            Omit to use the native default; None explicitly passes ().
        country : xs:string
            $country is used the specification to take into account country specific
            string representation.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:format-dateTime``.

        Notes
        -----
        Dates before October 15, 1582 (the start of the Gregorian calendar) will not
        return the correct dateTime value.
        If the specified picture string includes a fractional second width that is seven
        or more decimal places, then the fractional seconds are truncated (not rounded)
        on the seventh and greater width.

        Native reference: https://docs.marklogic.com/fn:format-dateTime
        """
        return _optional_call(
            "fn:format-dateTime", value, picture, language, calendar, country,
        )

    @staticmethod
    def format_number(value, picture, *, decimal_format_name=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns a formatted string representation of value argument based on the
        supplied picture.

        Parameters
        ----------
        value : xs:double
            The given numeric $value that needs to be formatted.
        picture : xs:string
            The desired string representation of the given number $value . The picture
            string is a sequence of characters, in which the characters represent
            variables such as, decimal-separator-sign, grouping-sign, zero-digit-sign,
            digit-sign, pattern-separator, percent sign and per-mille-sign. For details
            on the format-number picture string, see
            http://www.w3.org/TR/xslt20/#function-format-number .
        decimal_format_name : xs:string
            Represents a named <xsl:decimal-format> instruction. It is used to assign
            values to the variables mentioned above based on the picture string.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:format-number``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:format-number
        """
        return _optional_call("fn:format-number", value, picture, decimal_format_name)

    @staticmethod
    def format_time(
        value, picture, *, language=UNSET, calendar=UNSET, country=UNSET,
    ) -> Expr:
        """Build a native XQuery expression.

        Returns a formatted time value based on the picture argument.

        Parameters
        ----------
        value : xs:time
            The given time $value that needs to be formatted.
        picture : xs:string
            The desired string representation of the given time $value . The picture
            string is a sequence of characters, in which the characters represent
            variables such as, decimal-separator-sign, grouping-sign, zero-digit-sign,
            digit-sign, pattern-separator, percent sign and per-mille-sign. For details
            on the picture string, see http://www.w3.org/TR/xslt20/#date-picture-string
            .
        language : xs:string
            The desired language for string representation of the time $value .
            Omit to use the native default; None explicitly passes ().
        calendar : xs:string
            The only calendar supported at this point is "Gregorian" or "AD".
            Omit to use the native default; None explicitly passes ().
        country : xs:string
            $country is used the specification to take into account country specific
            string representation.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:format-time``.

        Notes
        -----
        If the specified picture string includes a fractional second width that is seven
        or more decimal places, then the fractional seconds are truncated (not rounded)
        on the seventh and greater width.

        Native reference: https://docs.marklogic.com/fn:format-time
        """
        return _optional_call(
            "fn:format-time", value, picture, language, calendar, country,
        )

    @staticmethod
    def function_arity(function) -> Expr:
        """Build a native XQuery expression.

        Returns the arity of the function(s) that the argument refers to.

        Parameters
        ----------
        function : function(*)
            The function value.

        Returns
        -------
        Expr
            Composable call to ``fn:function-arity``.

        Notes
        -----
        Function arguments must be XQuery Expr values, not Python callables.
        Native reference: https://docs.marklogic.com/fn:function-arity
        """
        return _FunctionCall("fn:function-arity", (function,))

    @staticmethod
    def function_available(function_name, *, arity=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns true if and only if there is an XQuery or XSLT function whose name and
        optionally arity matches the value of the $function-name and the optional $arity
        arguments.

        Parameters
        ----------
        function_name : xs:string
            The $function-name is a string containing a lexical QName. It may be a name
            of a builtin-type, type imported using xsl:import-schema, or an extension
            type. This parameter is mandatory. The lexical QName is expanded using the
            namespace declarations in scope for the expression. If the lexical QName is
            unprefixed, then the standard function namespace is used in the expanded
            QName.
        arity : xs:integer
            If $arity parameter is present, then the function returns true if and only
            if the function specified by the first argument has a signature that takes
            $arity number of arguments.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:function-available``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:function-available
        """
        return _optional_call("fn:function-available", function_name, arity)

    @staticmethod
    def function_lookup(name, arity) -> Expr:
        """Build a native XQuery expression.

        Returns a function with the given name and arity, or the empty sequence if none
        exists.

        Parameters
        ----------
        name : xs:QName
            The QName of the function.
        arity : xs:integer
            The number of arguments the function takes.

        Returns
        -------
        Expr
            Composable call to ``fn:function-lookup``.

        Notes
        -----
        Function arguments must be XQuery Expr values, not Python callables.
        Native reference: https://docs.marklogic.com/fn:function-lookup
        """
        return _FunctionCall("fn:function-lookup", (name, arity))

    @staticmethod
    def function_name(function) -> Expr:
        """Build a native XQuery expression.

        Returns the QName of the function(s) that the argument refers to.

        Parameters
        ----------
        function : function(*)
            The function value.
            ---

        Returns
        -------
        Expr
            Composable call to ``fn:function-name``.

        Notes
        -----
        Function arguments must be XQuery Expr values, not Python callables.
        Native reference: https://docs.marklogic.com/fn:function-name
        """
        return _FunctionCall("fn:function-name", (function,))

    @staticmethod
    def generate_id(node=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns a string that uniquely identifies a given node.

        Parameters
        ----------
        node : node()?
            The node whose ID will be generated.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:generate-id``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:generate-id
        """
        return _optional_call("fn:generate-id", node)

    @staticmethod
    def head(seq) -> Expr:
        """Build a native XQuery expression.

        Returns the first item in a sequence.

        Parameters
        ----------
        seq : item()*
            A sequence of items.

        Returns
        -------
        Expr
            Composable call to ``fn:head``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:head
        """
        return _FunctionCall("fn:head", (seq,))

    @staticmethod
    def hours_from_date_time(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:integer between 0 and 23, both inclusive, representing the hours
        component in the localized value of $arg.

        Parameters
        ----------
        arg : xs:dateTime?
            The dateTime whose hours component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:hours-from-dateTime``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:hours-from-dateTime
        """
        return _FunctionCall("fn:hours-from-dateTime", (arg,))

    @staticmethod
    def hours_from_duration(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:integer representing the hours component in the canonical lexical
        representation of the value of $arg.

        Parameters
        ----------
        arg : xs:duration?
            The duration whose hour component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:hours-from-duration``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:hours-from-duration
        """
        return _FunctionCall("fn:hours-from-duration", (arg,))

    @staticmethod
    def hours_from_time(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:integer between 0 and 23, both inclusive, representing the value
        of the hours component in the localized value of $arg.

        Parameters
        ----------
        arg : xs:time?
            The time whose hours component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:hours-from-time``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:hours-from-time
        """
        return _FunctionCall("fn:hours-from-time", (arg,))

    @staticmethod
    def id(arg, *, node=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns the sequence of element nodes that have an ID value matching the value
        of one or more of the IDREF values supplied in $arg.

        Parameters
        ----------
        arg : xs:string*
            The IDs of the elements to return.
        node : node()
            The target node.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:id``.

        Notes
        -----
        The function returns a sequence, in document order with duplicates eliminated,
        containing every element node E that satisfies all the following conditions:
        E is in the target document. The target document is the document containing
        $node, or the document containing the context node if the second argument is
        omitted. An error is raised [err:FODC0001] if $node, or the context item if the
        second argument is omitted, is a node in a tree whose root is not a document
        node or if the second argument is omitted and there is no context item
        [err:FONC0001], or if the context item is not a node [err:FOTY0011]. E has an ID
        value equal to one of the candidate IDREF values, where: An element has an ID
        value equal to V if either or both of the following conditions are true: The is-
        id property (See Section 5.5 is-id AccessorDM.) of the element node is true, and
        the typed value of the element node is equal to V under the rules of the eq
        operator using the Unicode code point collation (http://www.w3.org/2005/xpath-
        functions/collation/codepoint). The element has an attribute node whose is-id
        property (See Section 5.5 is-id AccessorDM.) is true and whose typed value is
        equal to V under the rules of the eq operator using the Unicode code point
        collation (http://www.w3.org/2005/xpath-functions/collation/codepoint). Each
        xs:string in $arg is parsed as if it were of type IDREFS, that is, each
        xs:string in $arg is treated as a space-separated sequence of tokens, each
        acting as an IDREF. These tokens are then included in the list of candidate
        IDREFs. If any of the tokens is not a lexically valid IDREF (that is, if it is
        not lexically an xs:NCName), it is ignored. Formally, The candidate IDREF values
        are the strings in the sequence given by the expression: for $s in $arg return
        fn:tokenize(fn:normalize-space($s), ' ') [. castable as xs:IDREF] If several
        elements have the same ID value, then E is the one that is first in document
        order.

        Notes
        -----
        If the data model is constructed from an Infoset, an attribute will have the is-
        id property if the corresponding attribute in the Infoset had an attribute type
        of ID: typically this means the attribute was declared as an ID in a DTD.
        If the data model is constructed from a PSVI, an element or attribute will have
        the is-id property if its schema-defined type is xs:ID or a type derived by
        restriction from xs:ID.
        No error is raised in respect of a candidate IDREF value that does not match the
        ID of any element in the document. If no candidate IDREF value matches the ID
        value of any element, the function returns the empty sequence.
        It is not necessary that the supplied argument should have type xs:IDREF or
        xs:IDREFS, or that it should be derived from a node with the is-idrefs property.
        An element may have more than one ID value. This can occur with synthetic data
        models or with data models constructed from a PSVI where an the element and one
        of its attributes are both typed as xs:ID.
        If the source document is well-formed but not valid, it is possible for two or
        more elements to have the same ID value. In this situation, the function will
        select the first such element.
        It is also possible in a well-formed but invalid document to have an element or
        attribute that has the is-id property but whose value does not conform to the
        lexical rules for the xs:ID type. Such a node will never be selected by this
        function.

        Native reference: https://docs.marklogic.com/fn:id
        """
        return _optional_call("fn:id", arg, node)

    @staticmethod
    def idref(arg, *, node=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns the sequence of element or attribute nodes that have an IDREF value
        matching the value of one or more of the ID values supplied in $arg.

        Parameters
        ----------
        arg : xs:string*
            The IDREFs of the elements and attributes to return.
        node : node()
            The target node.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:idref``.

        Notes
        -----
        The function returns a sequence, in document order with duplicates eliminated,
        containing every element or attribute node $N that satisfies all the following
        // conditions:
        $N is in the target document. The target document is the document containing
        $node, or the document containing the context node if the second argument is
        omitted. An error is raised [err:FODC0001] if $node, or the context item if the
        second argument is omitted, is a node in a tree whose root is not a document
        node or if the second argument is omitted and there is no context item
        [err:FONC0001], or if the context item is not a node [err:FOTY0011]. $N has an
        IDREF value equal to one of the candidate ID values, where: A node $N has an
        IDREF value equal to V if either or both of the following conditions are true:
        The is-idrefs property (See Section 5.6 is-idref AccessorDM.) of $N is true. The
        sequence fn:tokenize(fn:normalize-space($N), ' ') contains a string that is
        equal to V under the rules of the eq operator using the Unicode code point
        collation (http://www.w3.org/2005/xpath-functions/collation/codepoint). Each
        xs:string in $arg is parsed as if it were of type xs:ID. These xs:strings are
        then included in the list of candidate xs:IDs. If any of the xs:strings in $arg
        is not a lexically valid xs:ID (that is, if it is not lexically an xs:NCName),
        it is ignored. More formally, The candidate ID values are the strings in the
        sequence $arg[. castable as xs:ID]

        Notes
        -----
        An element or attribute typically acquires the is-idrefs property by being
        validated against the schema type xs:IDREF or xs:IDREFS, or (for attributes
        only) by being described as of type IDREF or IDREFS in a DTD.
        No error is raised in respect of a candidate ID value that does not match the
        IDREF value of any element or attribute in the document. If no candidate ID
        value matches the IDREF value of any element or attribute, the function returns
        the empty sequence.
        It is possible for two or more nodes to have an IDREF value that matches a given
        candidate ID value. In this situation, the function will return all such nodes.
        However, each matching node will be returned at most once, regardless how many
        candidate ID values it matches.
        It is possible in a well-formed but invalid document to have a node whose is-
        idrefs property is true but that does not conform to the lexical rules for the
        xs:IDREF type. The effect of the above rules is that ill-formed candidate ID
        values and ill-formed IDREF values are ignored

        Native reference: https://docs.marklogic.com/fn:idref
        """
        return _optional_call("fn:idref", arg, node)

    @staticmethod
    def implicit_timezone() -> Expr:
        """Build a native XQuery expression.

        Returns the value of the implicit timezone property from the dynamic context.

        Returns
        -------
        Expr
            Composable call to ``fn:implicit-timezone``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:implicit-timezone
        """
        return _FunctionCall("fn:implicit-timezone")

    @staticmethod
    def in_scope_prefixes(element) -> Expr:
        """Build a native XQuery expression.

        Returns the prefixes of the in-scope namespaces for $element.

        Parameters
        ----------
        element : element()
            The element whose in-scope prefixes will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:in-scope-prefixes``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:in-scope-prefixes
        """
        return _FunctionCall("fn:in-scope-prefixes", (element,))

    @staticmethod
    def index_of(seq_param, srch_param, *, collation_literal=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns a sequence of positive integers giving the positions within the sequence
        $seqParam of items that are equal to $srchParam.

        Parameters
        ----------
        seq_param : xs:anyAtomicType*
            A sequence of values.
        srch_param : xs:anyAtomicType
            A value to find on the list.
        collation_literal : xs:string
            A collation identifier.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:index-of``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:index-of
        """
        return _optional_call("fn:index-of", seq_param, srch_param, collation_literal)

    @staticmethod
    def insert_before(target, position, inserts) -> Expr:
        """Build a native XQuery expression.

        Returns a new sequence constructed from the value of $target with the value of
        $inserts inserted at the position specified by the value of $position.

        Parameters
        ----------
        target : item()*
            The sequence of items into which new items will be inserted.
        position : xs:integer
            The position in the target sequence at which the new items will be added.
        inserts : item()*
            The items to insert into the target sequence.

        Returns
        -------
        Expr
            Composable call to ``fn:insert-before``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:insert-before
        """
        return _FunctionCall("fn:insert-before", (target, position, inserts))

    @staticmethod
    def iri_to_uri(uri_part) -> Expr:
        """Build a native XQuery expression.

        Idempotent function that escapes non-URI characters.

        Parameters
        ----------
        uri_part : xs:string
            A string representing an unescaped URI.

        Returns
        -------
        Expr
            Composable call to ``fn:iri-to-uri``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:iri-to-uri
        """
        return _FunctionCall("fn:iri-to-uri", (uri_part,))

    @staticmethod
    def key(key_name, key_value, *, top=UNSET) -> Expr:
        """Build a native XQuery expression.

        The key function does for keys what the id function does for IDs.

        Parameters
        ----------
        key_name : xs:string
            The name of the key.
        key_value : xs:string
            The value of the key.
        top : node()
            The subtree to limit the results to.
            ---
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:key``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:key
        """
        return _optional_call("fn:key", key_name, key_value, top)

    @staticmethod
    def lang(testlang, *, node=UNSET) -> Expr:
        """Build a native XQuery expression.

        This function tests whether the language of $node, or the context node if the
        second argument is omitted, as specified by xml:lang attributes is the same as,
        or is a sublanguage of, the language specified by $testlang.

        Parameters
        ----------
        testlang : xs:string?
            The language against which to test the node.
        node : node()
            The node to test.
            ---
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:lang``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:lang
        """
        return _optional_call("fn:lang", testlang, node)

    @staticmethod
    def last() -> Expr:
        """Build a native XQuery expression.

        Returns the context size from the dynamic context.

        Returns
        -------
        Expr
            Composable call to ``fn:last``.

        Notes
        -----
        fn:last() returns the exact context position of the last item in the current
        context, so it must count all the items to do this. It is as much work as
        fn:count() . fn:last() is therefore best used to find the last item in a short
        context sequence. For example, it is useful in a path expression predicate to
        find the last child node of a particular element node in a particular document.
        Using fn:last() in a predicate expression is not an efficient way to extract a
        subsequence of large item sequence. Its use for this purpose is strongly
        discouraged. It is much more efficient to use fn:tail() or fn:subsequence()
        instead.

        Native reference: https://docs.marklogic.com/fn:last
        """
        return _FunctionCall("fn:last")

    @staticmethod
    def local_name(arg=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns the local part of the name of $arg as an xs:string that will either be
        the zero-length string or will have the lexical form of an xs:NCName.

        Parameters
        ----------
        arg : node()?
            The node whose local name is to be returned.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:local-name``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:local-name
        """
        return _optional_call("fn:local-name", arg)

    @staticmethod
    def local_name_from_qname(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:NCName representing the local part of $arg.

        Parameters
        ----------
        arg : xs:QName?
            A qualified name.

        Returns
        -------
        Expr
            Composable call to ``fn:local-name-from-QName``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:local-name-from-QName
        """
        return _FunctionCall("fn:local-name-from-QName", (arg,))

    @staticmethod
    def lower_case(string) -> Expr:
        """Build a native XQuery expression.

        Returns the specified string converting all of the characters to lower-case
        characters.

        Parameters
        ----------
        string : xs:string?
            The string to convert.

        Returns
        -------
        Expr
            Composable call to ``fn:lower-case``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:lower-case
        """
        return _FunctionCall("fn:lower-case", (string,))

    @staticmethod
    def map(function, seq) -> Expr:
        """Build a native XQuery expression.

        Applies the function item $function to every item from the sequence $seq in
        turn, returning the concatenation of the resulting sequences in order.

        Parameters
        ----------
        function : function(item()) as item()*
            The function value.
        seq : item()*
            The function value.

        Returns
        -------
        Expr
            Composable call to ``fn:map``.

        Notes
        -----
        Function arguments must be XQuery Expr values, not Python callables.
        Native reference: https://docs.marklogic.com/fn:map
        """
        return _FunctionCall("fn:map", (function, seq))

    @staticmethod
    def map_pairs(function, seq1, seq2) -> Expr:
        """Build a native XQuery expression.

        Applies the function item $function to successive pairs of items taken one from
        $seq1 and one from $seq2, returning the concatenation of the resulting sequences
        in order.

        Parameters
        ----------
        function : function(item(), item()) as item()*
            The map function value.
        seq1 : item()*
            The first sequence argument.
        seq2 : item()*
            The second sequence argument.

        Returns
        -------
        Expr
            Composable call to ``fn:map-pairs``.

        Notes
        -----
        Function arguments must be XQuery Expr values, not Python callables.
        Native reference: https://docs.marklogic.com/fn:map-pairs
        """
        return _FunctionCall("fn:map-pairs", (function, seq1, seq2))

    @staticmethod
    def matches(input, pattern, *, flags=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns true if the specified $input matches the specified $pattern, otherwise
        returns false.

        Parameters
        ----------
        input : xs:string?
            The input from which to match.
        pattern : xs:string
            The regular expression to match.
        flags : xs:string
            The flag representing how to interpret the regular expression. One of "s",
            "m", "i", or "x", as defined in http://www.w3.org/TR/xpath-functions/#flags
            .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:matches``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:matches
        """
        return _optional_call("fn:matches", input, pattern, flags)

    @staticmethod
    def max(arg, *, collation=UNSET) -> Expr:
        """Build a native XQuery expression.

        Selects an item from the input sequence $arg whose value is greater than or
        equal to the value of every other item in the input sequence.

        Parameters
        ----------
        arg : xs:anyAtomicType*
            The sequence of values whose maximum will be returned.
        collation : xs:string
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:max``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:max
        """
        return _optional_call("fn:max", arg, collation)

    @staticmethod
    def min(arg, *, collation=UNSET) -> Expr:
        """Build a native XQuery expression.

        Selects an item from the input sequence $arg whose value is less than or equal
        to the value of every other item in the input sequence.

        Parameters
        ----------
        arg : xs:anyAtomicType*
            The sequence of values whose minimum will be returned.
        collation : xs:string
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:min``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:min
        """
        return _optional_call("fn:min", arg, collation)

    @staticmethod
    def minutes_from_date_time(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:integer value between 0 and 59, both inclusive, representing the
        minute component in the localized value of $arg.

        Parameters
        ----------
        arg : xs:dateTime?
            The dateTime whose minutes component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:minutes-from-dateTime``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:minutes-from-dateTime
        """
        return _FunctionCall("fn:minutes-from-dateTime", (arg,))

    @staticmethod
    def minutes_from_duration(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:integer representing the minutes component in the canonical
        lexical representation of the value of $arg.

        Parameters
        ----------
        arg : xs:duration?
            The duration whose minute component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:minutes-from-duration``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:minutes-from-duration
        """
        return _FunctionCall("fn:minutes-from-duration", (arg,))

    @staticmethod
    def minutes_from_time(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:integer value between 0 to 59, both inclusive, representing the
        value of the minutes component in the localized value of $arg.

        Parameters
        ----------
        arg : xs:time?
            The time whose minutes component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:minutes-from-time``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:minutes-from-time
        """
        return _FunctionCall("fn:minutes-from-time", (arg,))

    @staticmethod
    def month_from_date(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:integer between 1 and 12, both inclusive, representing the month
        component in the localized value of $arg.

        Parameters
        ----------
        arg : xs:date?
            The date whose month component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:month-from-date``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:month-from-date
        """
        return _FunctionCall("fn:month-from-date", (arg,))

    @staticmethod
    def month_from_date_time(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:integer between 1 and 12, both inclusive, representing the month
        component in the localized value of $arg.

        Parameters
        ----------
        arg : xs:dateTime?
            The dateTime whose month component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:month-from-dateTime``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:month-from-dateTime
        """
        return _FunctionCall("fn:month-from-dateTime", (arg,))

    @staticmethod
    def months_from_duration(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:integer representing the months component in the canonical lexical
        representation of the value of $arg.

        Parameters
        ----------
        arg : xs:duration?
            The duration whose month component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:months-from-duration``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:months-from-duration
        """
        return _FunctionCall("fn:months-from-duration", (arg,))

    @staticmethod
    def name(arg=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns the name of a node, as an xs:string that is either the zero-length
        string, or has the lexical form of an xs:QName.

        Parameters
        ----------
        arg : node()?
            The node whose name is to be returned.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:name``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:name
        """
        return _optional_call("fn:name", arg)

    @staticmethod
    def namespace_uri(arg=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns the namespace URI of the xs:QName of the node specified by $arg.

        Parameters
        ----------
        arg : node()?
            The node whose namespace URI is to be returned.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:namespace-uri``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:namespace-uri
        """
        return _optional_call("fn:namespace-uri", arg)

    @staticmethod
    def namespace_uri_for_prefix(prefix, element) -> Expr:
        """Build a native XQuery expression.

        Returns the namespace URI of one of the in-scope namespaces for $element,
        identified by its namespace prefix.

        Parameters
        ----------
        prefix : xs:string?
            A namespace prefix to look up.
        element : element()
            An element node providing namespace context.

        Returns
        -------
        Expr
            Composable call to ``fn:namespace-uri-for-prefix``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:namespace-uri-for-prefix
        """
        return _FunctionCall("fn:namespace-uri-for-prefix", (prefix, element))

    @staticmethod
    def namespace_uri_from_qname(arg) -> Expr:
        """Build a native XQuery expression.

        Returns the namespace URI for $arg as an xs:string.

        Parameters
        ----------
        arg : xs:QName?
            A qualified name.

        Returns
        -------
        Expr
            Composable call to ``fn:namespace-uri-from-QName``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:namespace-uri-from-QName
        """
        return _FunctionCall("fn:namespace-uri-from-QName", (arg,))

    @staticmethod
    def nilled(arg) -> Expr:
        """Build a native XQuery expression.

        Summary: Returns an xs:boolean indicating whether the argument node is "nilled".

        Parameters
        ----------
        arg : node()?
            The node to test for nilled status.

        Returns
        -------
        Expr
            Composable call to ``fn:nilled``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:nilled
        """
        return _FunctionCall("fn:nilled", (arg,))

    @staticmethod
    def node_kind(node) -> Expr:
        """Build a native XQuery expression.

        [0.9-ml only, use xdmp:node-kind in 1.0 and 1.0-ml] Returns an xs:string
        representing the node's kind: either "document", "element", "attribute", "text",
        "namespace", "processing-instruction", "binary", or "comment".

        Parameters
        ----------
        node : node()?
            The node whose kind is to be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:node-kind``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:node-kind
        """
        return _FunctionCall("fn:node-kind", (node,))

    @staticmethod
    def node_name(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an expanded-QName for node kinds that can have names.

        Parameters
        ----------
        arg : node()?
            The node whose name is to be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:node-name``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:node-name
        """
        return _FunctionCall("fn:node-name", (arg,))

    @staticmethod
    def normalize_space(input=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns the specified string with normalized whitespace, which strips off any
        leading or trailing whitespace and replaces any other sequences of more than one
        whitespace characters with a single space character (#x20).

        Parameters
        ----------
        input : xs:string?
            The string from which to normalize whitespace.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:normalize-space``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:normalize-space
        """
        return _optional_call("fn:normalize-space", input)

    @staticmethod
    def normalize_unicode(arg, *, normalization_form=UNSET) -> Expr:
        """Build a native XQuery expression.

        Return the argument normalized according to the normalization criteria for a
        normalization form identified by the value of $normalizationForm.

        Parameters
        ----------
        arg : xs:string?
            The string to normalize.
        normalization_form : xs:string
            The form under which to normalize the specified string: NFC, NFD, NFKC, or
            NFKD.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:normalize-unicode``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:normalize-unicode
        """
        return _optional_call("fn:normalize-unicode", arg, normalization_form)

    @staticmethod
    def not_(arg) -> Expr:
        """Build a native XQuery expression.

        Returns true if the effective boolean value is false, and false if the effective
        boolean value is true.

        Parameters
        ----------
        arg : item()*
            The expression to negate.

        Returns
        -------
        Expr
            Composable call to ``fn:not``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:not
        """
        return _FunctionCall("fn:not", (arg,))

    @staticmethod
    def number(arg=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns the value indicated by $arg or, if $arg is not specified, the context
        item after atomization, converted to an xs:double.

        Parameters
        ----------
        arg : xs:anyAtomicType?
            The value to be returned as an xs:double value.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:number``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:number
        """
        return _optional_call("fn:number", arg)

    @staticmethod
    def one_or_more(arg) -> Expr:
        """Build a native XQuery expression.

        Returns $arg if it contains one or more items.

        Parameters
        ----------
        arg : item()*
            The sequence of items.

        Returns
        -------
        Expr
            Composable call to ``fn:one-or-more``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:one-or-more
        """
        return _FunctionCall("fn:one-or-more", (arg,))

    @staticmethod
    def position() -> Expr:
        """Build a native XQuery expression.

        Returns the context position from the dynamic context.

        Returns
        -------
        Expr
            Composable call to ``fn:position``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:position
        """
        return _FunctionCall("fn:position")

    @staticmethod
    def prefix_from_qname(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:NCName representing the prefix of $arg.

        Parameters
        ----------
        arg : xs:QName?
            A qualified name.

        Returns
        -------
        Expr
            Composable call to ``fn:prefix-from-QName``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:prefix-from-QName
        """
        return _FunctionCall("fn:prefix-from-QName", (arg,))

    @staticmethod
    def qname(uri, lexical) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:QName with the namespace URI given in $paramURI.

        Parameters
        ----------
        uri : xs:string?
            A namespace URI, as a string.
        lexical : xs:string
            A lexical qualified name (xs:QName), a string of the form "prefix:localname"
            or "localname".

        Returns
        -------
        Expr
            Composable call to ``fn:QName``.

        Notes
        -----
        If $paramQName does not have the correct lexical form for xs:QName an error is
        raised [err:FOCA0002].
        Note that unlike xs:QName this function does not require an xs:string literal as
        the argument.

        Native reference: https://docs.marklogic.com/fn:QName
        """
        return _FunctionCall("fn:QName", (uri, lexical))

    @staticmethod
    def regex_group(group_number) -> Expr:
        """Build a native XQuery expression.

        While the xsl:matching-substring instruction is active, a set of current
        captured substrings is available, corresponding to the parenthesized sub-
        expressions of the regular expression.

        Parameters
        ----------
        group_number : xs:integer
            The group number to return.

        Returns
        -------
        Expr
            Composable call to ``fn:regex-group``.

        Notes
        -----
        The function returns the zero-length string if there is no captured substring
        with the relevant number. This can occur for a number of reasons:
        The number is negative. The regular expression does not contain a parenthesized
        sub-expression with the given number. The parenthesized sub-expression exists,
        and did not match any part of the input string. The parenthesized sub-expression
        exists, and matched a zero-length substring of the input string.
        ---

        Native reference: https://docs.marklogic.com/fn:regex-group
        """
        return _FunctionCall("fn:regex-group", (group_number,))

    @staticmethod
    def remove(target, position) -> Expr:
        """Build a native XQuery expression.

        Returns a new sequence constructed from the value of $target with the item at
        the position specified by the value of $position removed.

        Parameters
        ----------
        target : item()*
            The sequence of items from which items will be removed.
        position : xs:integer
            The position in the target sequence from which the items will be removed.

        Returns
        -------
        Expr
            Composable call to ``fn:remove``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:remove
        """
        return _FunctionCall("fn:remove", (target, position))

    @staticmethod
    def replace(input, pattern, replacement, *, flags=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns a string constructed by replacing the specified $pattern on the $input
        string with the specified $replacement string.

        Parameters
        ----------
        input : xs:string?
            The string to start with.
        pattern : xs:string
            The regular expression pattern to match. If the pattern does not match the
            $input string, the function will return the $input string unchanged.
        replacement : xs:string
            The regular expression pattern to replace the $pattern with. It can also be
            a capture expression (for more details, see http://www.w3.org/TR/xpath-
            functions/#func-replace ).
        flags : xs:string
            The flag representing how to interpret the regular expression. One of "s",
            "m", "i", or "x", as defined in http://www.w3.org/TR/xpath-functions/#flags
            .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:replace``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:replace
        """
        return _optional_call("fn:replace", input, pattern, replacement, flags)

    @staticmethod
    def resolve_qname(qname, element) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:QName value (that is, an expanded QName) by taking an xs:string
        that has the lexical form of an xs:QName (a string in the form "prefix:local-
        name" or "local-name") and resolving it using the in-scope namespaces for a
        given element.

        Parameters
        ----------
        qname : xs:string?
            A string of the form "prefix:local-name".
        element : element()
            An element providing the in-scope namespaces to use to resolve the qualified
            name.

        Returns
        -------
        Expr
            Composable call to ``fn:resolve-QName``.

        Notes
        -----
        Sometimes the requirement is to construct an xs:QName without using the default
        namespace. This can be achieved by writing:
        if ( fn:contains($qname, ":") ) then ( fn:resolve-QName($qname, $element) ) else
        ( fn:QName("", $qname) )
        If the requirement is to construct an xs:QName using the namespaces in the
        static context, then the xs:QName constructor should be used.
        If $qname does not have the correct lexical form for xs:QName an error is raised
        [err:FOCA0002].
        If $qname is the empty sequence, returns the empty sequence.
        More specifically, the function searches the namespace bindings of $element for
        a binding whose name matches the prefix of $qname, or the zero-length string if
        it has no prefix, and constructs an expanded QName whose local name is taken
        from the supplied $qname, and whose namespace URI is taken from the string value
        of the namespace binding.
        If the $qname has a prefix and if there is no namespace binding for $element
        that matches this prefix, then an error is raised [err:FONS0004].
        If the $qname has no prefix, and there is no namespace binding for $element
        corresponding to the default (unnamed) namespace, then the resulting expanded
        QName has no namespace part.
        The prefix (or absence of a prefix) in the supplied $qname argument is retained
        in the returned expanded QName, as discussed in Section 2.1 Terminology[DM].

        Native reference: https://docs.marklogic.com/fn:resolve-QName
        """
        return _FunctionCall("fn:resolve-QName", (qname, element))

    @staticmethod
    def resolve_uri(relative, *, base=UNSET) -> Expr:
        """Build a native XQuery expression.

        Resolves a relative URI against an absolute URI.

        Parameters
        ----------
        relative : xs:string?
            A URI reference to resolve against the base.
        base : xs:string
            An absolute URI to use as the base of the resolution.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:resolve-uri``.

        Notes
        -----
        If $base is specified, it is assumed to be an absolute URI and $relative is
        assumed to be an absolute or a relative URI reference. If $relative is a
        relative URI reference, it is resolved against $base, using an algorithm such as
        the ones described in [ RFC 2396 ] or [ RFC 3986 ], and the resulting absolute
        URI reference is returned.
        If $relative is the zero-length string, fn:resolve-uri returns the value of
        $base, or the base-uri property from the static context if there is no $base
        value specified (if the base-uri property is not initialized in the static
        context, an error is raised).
        Resolving a URI does not dereference it. This is merely a syntactic operation on
        two character strings.

        Native reference: https://docs.marklogic.com/fn:resolve-uri
        """
        return _optional_call("fn:resolve-uri", relative, base)

    @staticmethod
    def reverse(target) -> Expr:
        """Build a native XQuery expression.

        Reverses the order of items in a sequence.

        Parameters
        ----------
        target : item()*
            The sequence of items to be reversed.

        Returns
        -------
        Expr
            Composable call to ``fn:reverse``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:reverse
        """
        return _FunctionCall("fn:reverse", (target,))

    @staticmethod
    def root(arg=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns the root of the tree to which $arg belongs.

        Parameters
        ----------
        arg : node()?
            The node whose root node will be returned.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:root``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:root
        """
        return _optional_call("fn:root", arg)

    @staticmethod
    def round(arg) -> Expr:
        """Build a native XQuery expression.

        Returns the number with no fractional part that is closest to the argument.

        Parameters
        ----------
        arg : numeric?
            A numeric value to round.

        Returns
        -------
        Expr
            Composable call to ``fn:round``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:round
        """
        return _FunctionCall("fn:round", (arg,))

    @staticmethod
    def round_half_to_even(arg, *, precision=UNSET) -> Expr:
        """Build a native XQuery expression.

        The value returned is the nearest (that is, numerically closest) numeric to $arg
        that is a multiple of ten to the power of minus $precision.

        Parameters
        ----------
        arg : numeric?
            A numeric value to round.
        precision : xs:integer
            The precision to which to round the value.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:round-half-to-even``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:round-half-to-even
        """
        return _optional_call("fn:round-half-to-even", arg, precision)

    @staticmethod
    def seconds_from_date_time(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:decimal value between 0 and 60.999..., both inclusive representing
        the seconds and fractional seconds in the localized value of $arg.

        Parameters
        ----------
        arg : xs:dateTime?
            The dateTime whose seconds component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:seconds-from-dateTime``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:seconds-from-dateTime
        """
        return _FunctionCall("fn:seconds-from-dateTime", (arg,))

    @staticmethod
    def seconds_from_duration(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:decimal representing the seconds component in the canonical
        lexical representation of the value of $arg.

        Parameters
        ----------
        arg : xs:duration?
            The duration whose minute component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:seconds-from-duration``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:seconds-from-duration
        """
        return _FunctionCall("fn:seconds-from-duration", (arg,))

    @staticmethod
    def seconds_from_time(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:decimal value between 0 and 60.999..., both inclusive,
        representing the seconds and fractional seconds in the localized value of $arg.

        Parameters
        ----------
        arg : xs:time?
            The time whose seconds component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:seconds-from-time``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:seconds-from-time
        """
        return _FunctionCall("fn:seconds-from-time", (arg,))

    @staticmethod
    def starts_with(parameter1, parameter2, *, collation=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns true if the first parameter starts with the string from the second
        parameter, otherwise returns false.

        Parameters
        ----------
        parameter1 : xs:string?
            The string from which to test.
        parameter2 : xs:string?
            The string to test whether it is at the beginning of the first parameter.
        collation : xs:string
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:starts-with``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:starts-with
        """
        return _optional_call("fn:starts-with", parameter1, parameter2, collation)

    @staticmethod
    def static_base_uri() -> Expr:
        """Build a native XQuery expression.

        Returns the value of the base-uri property from the static context.

        Returns
        -------
        Expr
            Composable call to ``fn:static-base-uri``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:static-base-uri
        """
        return _FunctionCall("fn:static-base-uri")

    @staticmethod
    def string(arg=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns the value of $arg represented as an xs:string.

        Parameters
        ----------
        arg : item()?
            The item to be rendered as a string.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:string``.

        Notes
        -----
        If $arg is the empty sequence, the zero-length string is returned.
        If $arg is a node, the function returns the string-value of the node, as
        obtained using the dm:string-value accessor.
        $arg cast as xs:string

        Native reference: https://docs.marklogic.com/fn:string
        """
        return _optional_call("fn:string", arg)

    @staticmethod
    def string_join(parameter1, parameter2) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:string created by concatenating the members of the $parameter1
        sequence using $parameter2 as a separator.

        Parameters
        ----------
        parameter1 : xs:string*
            A sequence of strings.
        parameter2 : xs:string
            A separator string to concatenate between the items in $parameter1.

        Returns
        -------
        Expr
            Composable call to ``fn:string-join``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:string-join
        """
        return _FunctionCall("fn:string-join", (parameter1, parameter2))

    @staticmethod
    def string_length(source_string=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns an integer representing the length of the specified string.

        Parameters
        ----------
        source_string : xs:string?
            The string to calculate the length.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:string-length``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:string-length
        """
        return _optional_call("fn:string-length", source_string)

    @staticmethod
    def string_pad(pad_string, pad_count) -> Expr:
        """Build a native XQuery expression.

        [0.9-ml only] Returns a string representing the $padString concatenated with
        itself the number of times specified in $padCount.

        Parameters
        ----------
        pad_string : xs:string?
            The string to pad.
        pad_count : xs:integer
            The number of times to pad the string.

        Returns
        -------
        Expr
            Composable call to ``fn:string-pad``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:string-pad
        """
        return _FunctionCall("fn:string-pad", (pad_string, pad_count))

    @staticmethod
    def string_to_codepoints(arg) -> Expr:
        """Build a native XQuery expression.

        Returns the sequence of Unicode code points that constitute an xs:string.

        Parameters
        ----------
        arg : xs:string
            A string.

        Returns
        -------
        Expr
            Composable call to ``fn:string-to-codepoints``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:string-to-codepoints
        """
        return _FunctionCall("fn:string-to-codepoints", (arg,))

    @staticmethod
    def subsequence(source_seq, starting_loc, *, length=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns the contiguous sequence of items in the value of $sourceSeq beginning at
        the position indicated by the value of $startingLoc and continuing for the
        number of items indicated by the value of $length.

        Parameters
        ----------
        source_seq : item()*
            The sequence of items from which a subsequence will be selected.
        starting_loc : xs:double
            The starting position of the start of the subsequence.
        length : xs:double
            The length of the subsequence.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:subsequence``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:subsequence
        """
        return _optional_call("fn:subsequence", source_seq, starting_loc, length)

    @staticmethod
    def substring(source_string, starting_loc, *, length=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns a substring starting from the $startingLoc and continuing for $length
        characters.

        Parameters
        ----------
        source_string : xs:string?
            The string from which to create a substring.
        starting_loc : xs:double
            The number of characters from the start of the $sourceString.
        length : xs:double
            The number of characters beyond the $startingLoc.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:substring``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:substring
        """
        return _optional_call("fn:substring", source_string, starting_loc, length)

    @staticmethod
    def substring_after(input, after, *, collation=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns the substring created by taking all of the input characters that occur
        after the specified $after characters.

        Parameters
        ----------
        input : xs:string?
            The string from which to create the substring.
        after : xs:string?
            The string after which the substring is created.
        collation : xs:string
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:substring-after``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:substring-after
        """
        return _optional_call("fn:substring-after", input, after, collation)

    @staticmethod
    def substring_before(input, before, *, collation=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns the substring created by taking all of the input characters that occur
        before the specified $before characters.

        Parameters
        ----------
        input : xs:string?
            The string from which to create the substring.
        before : xs:string?
            The string before which the substring is created.
        collation : xs:string
            The optional name of a valid collation URI. For information on the collation
            URI syntax, see the Search Developer's Guide .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:substring-before``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:substring-before
        """
        return _optional_call("fn:substring-before", input, before, collation)

    @staticmethod
    def subtract_date_times_yielding_day_time_duration(srcval1, srcval2) -> Expr:
        """Build a native XQuery expression.

        [0.9-ml only, use the minus operator ( - ) instead] Returns the
        xdt:dayTimeDuration that corresponds to the difference between the normalized
        value of $srcval1 and the normalized value of $srcval2.

        Parameters
        ----------
        srcval1 : xs:dateTime
            The second xs:dateTime value.
        srcval2 : xs:dateTime
            The second xs:dateTime value.

        Returns
        -------
        Expr
            Composable call to ``fn:subtract-dateTimes-yielding-dayTimeDuration``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:subtract-dateTimes-yielding-dayTimeDuration
        """
        return _FunctionCall(
            "fn:subtract-dateTimes-yielding-dayTimeDuration", (srcval1, srcval2),
        )

    @staticmethod
    def subtract_date_times_yielding_year_month_duration(srcval1, srcval2) -> Expr:
        """Build a native XQuery expression.

        [0.9-ml only, use the minus operator ( - ) instead] Returns the
        xdt:yearMonthDuration that corresponds to the difference between the normalized
        value of $srcval1 and the normalized value of $srcval2.

        Parameters
        ----------
        srcval1 : xs:dateTime
            The second xs:dateTime value.
        srcval2 : xs:dateTime
            The second xs:dateTime value.

        Returns
        -------
        Expr
            Composable call to ``fn:subtract-dateTimes-yielding-yearMonthDuration``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:subtract-dateTimes-yielding-yearMonthDuration
        """
        return _FunctionCall(
            "fn:subtract-dateTimes-yielding-yearMonthDuration", (srcval1, srcval2),
        )

    @staticmethod
    def sum(arg, *, zero=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns a value obtained by adding together the values in $arg.

        Parameters
        ----------
        arg : xs:anyAtomicType*
            The sequence of values to be summed.
        zero : xs:anyAtomicType?
            The value to return as zero if the input sequence is the empty sequence.
            This parameter is not available in the 0.9-ml XQuery dialect.
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:sum``.

        Notes
        -----
        fn:sum

        Native reference: https://docs.marklogic.com/fn:sum
        """
        return _optional_call("fn:sum", arg, zero)

    @staticmethod
    def system_property(property_name) -> Expr:
        """Build a native XQuery expression.

        Returns a string representing the value of the system property identified by the
        name.

        Parameters
        ----------
        property_name : xs:string
            The name of the property whose value is to be returned. Valid names are:
            xsl:version xsl:vendor xsl:vendor-url xsl:product-name xsl:product-version
            xsl:is-schema-aware xsl:supports-serialization xsl:supports-backwards-
            compatibility xsl:supports-namespace-axis

        Returns
        -------
        Expr
            Composable call to ``fn:system-property``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:system-property
        """
        return _FunctionCall("fn:system-property", (property_name,))

    @staticmethod
    def tail(seq) -> Expr:
        """Build a native XQuery expression.

        Returns all but the first item in a sequence.

        Parameters
        ----------
        seq : item()*
            The function value.

        Returns
        -------
        Expr
            Composable call to ``fn:tail``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:tail
        """
        return _FunctionCall("fn:tail", (seq,))

    @staticmethod
    def timezone_from_date(arg) -> Expr:
        """Build a native XQuery expression.

        Returns the timezone component of $arg if any.

        Parameters
        ----------
        arg : xs:date?
            The date whose timezone component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:timezone-from-date``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:timezone-from-date
        """
        return _FunctionCall("fn:timezone-from-date", (arg,))

    @staticmethod
    def timezone_from_date_time(arg) -> Expr:
        """Build a native XQuery expression.

        Returns the timezone component of $arg if any.

        Parameters
        ----------
        arg : xs:dateTime?
            The dateTime whose timezone component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:timezone-from-dateTime``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:timezone-from-dateTime
        """
        return _FunctionCall("fn:timezone-from-dateTime", (arg,))

    @staticmethod
    def timezone_from_time(arg) -> Expr:
        """Build a native XQuery expression.

        Returns the timezone component of $arg if any.

        Parameters
        ----------
        arg : xs:time?
            The time whose timezone component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:timezone-from-time``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:timezone-from-time
        """
        return _FunctionCall("fn:timezone-from-time", (arg,))

    @staticmethod
    def tokenize(input, pattern, *, flags=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns a sequence of strings constructed by breaking the specified input into
        substrings separated by the specified $pattern.

        Parameters
        ----------
        input : xs:string?
            The string to tokenize.
        pattern : xs:string
            The regular expression pattern from which to separate the tokens.
        flags : xs:string
            The flag representing how to interpret the regular expression. One of "s",
            "m", "i", or "x", as defined in http://www.w3.org/TR/xpath-functions/#flags
            .
            Omit to use the native default; None explicitly passes ().

        Returns
        -------
        Expr
            Composable call to ``fn:tokenize``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:tokenize
        """
        return _optional_call("fn:tokenize", input, pattern, flags)

    @staticmethod
    def trace(value, label) -> Expr:
        """Build a native XQuery expression.

        Return the input $value unchanged and, if $label is the name of an enabled
        server event, log event to the App Server log file
        <install_dir>/Logs/<port>_ErrorLog.txt; where <install_dir> is the MarkLogic
        install directory, and <port> is the port number of the current App Server or
        "TaskServer" if the current request is running on the Task Server.

        Parameters
        ----------
        value : item()*
            The values to trace.
        label : xs:string
            A string label for the trace output.

        Returns
        -------
        Expr
            Composable call to ``fn:trace``.

        Notes
        -----
        group_name

        Native reference: https://docs.marklogic.com/fn:trace
        """
        return _FunctionCall("fn:trace", (value, label))

    @staticmethod
    def translate(src, map_string, trans_string) -> Expr:
        """Build a native XQuery expression.

        Returns a string where every character in $src that occurs in some position in
        the $mapString is translated into the $transString character in the
        corresponding location of the $mapString character.

        Parameters
        ----------
        src : xs:string?
            The string to translate characters.
        map_string : xs:string?
            The string representing characters to be translated.
        trans_string : xs:string?
            The string representing the characters to which the $mapString characters
            are translated.

        Returns
        -------
        Expr
            Composable call to ``fn:translate``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:translate
        """
        return _FunctionCall("fn:translate", (src, map_string, trans_string))

    @staticmethod
    def true() -> Expr:
        """Build a native XQuery expression.

        Returns the xs:boolean value true.

        Returns
        -------
        Expr
            Composable call to ``fn:true``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:true
        """
        return _FunctionCall("fn:true")

    @staticmethod
    def type_available(type_name) -> Expr:
        """Build a native XQuery expression.

        Returns true if and only if there is a type whose name matches the value of the
        $type-name argument is present in the static context.

        Parameters
        ----------
        type_name : xs:string
            The $type-name is a string containing a lexical QName. It may be a name of a
            builtin-type, type imported using xsl:import-schema, or an extension type.
            This parameter is mandatory. The lexical QName is expanded using the
            namespace declarations in scope for the expression. If the lexical QName is
            unprefixed, then the default namespace is used in the expanded QName.

        Returns
        -------
        Expr
            Composable call to ``fn:type-available``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:type-available
        """
        return _FunctionCall("fn:type-available", (type_name,))

    @staticmethod
    def unordered(source_seq) -> Expr:
        """Build a native XQuery expression.

        Returns the items of $sourceSeq in an implementation dependent order.

        Parameters
        ----------
        source_seq : item()*
            The sequence of items.

        Returns
        -------
        Expr
            Composable call to ``fn:unordered``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:unordered
        """
        return _FunctionCall("fn:unordered", (source_seq,))

    @staticmethod
    def unparsed_entity_public_id(entity_name) -> Expr:
        """Build a native XQuery expression.

        Returns the public identifier of the unparsed entity specified by the $entity-
        name parameter.

        Parameters
        ----------
        entity_name : xs:string
            The entity name.
            ---

        Returns
        -------
        Expr
            Composable call to ``fn:unparsed-entity-public-id``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:unparsed-entity-public-id
        """
        return _FunctionCall("fn:unparsed-entity-public-id", (entity_name,))

    @staticmethod
    def unparsed_entity_uri(entity_name) -> Expr:
        """Build a native XQuery expression.

        Always returns the zero length string.

        Parameters
        ----------
        entity_name : xs:string
            The entity name.
            ---

        Returns
        -------
        Expr
            Composable call to ``fn:unparsed-entity-uri``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:unparsed-entity-uri
        """
        return _FunctionCall("fn:unparsed-entity-uri", (entity_name,))

    @staticmethod
    def unparsed_text(href, *, encoding=UNSET) -> Expr:
        """Build a native XQuery expression.

        Reads a file stored in the database as either text or binary file and returns
        its contents as a string.

        Parameters
        ----------
        href : xs:string
            The $href is a string containing a URI reference. It must identify a
            resource that can be read as text. If the URI is a relative URI then it is
            resolved relative to the base URI from the static context.
        encoding : xs:string
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
        Expr
            Composable call to ``fn:unparsed-text``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:unparsed-text
        """
        return _optional_call("fn:unparsed-text", href, encoding)

    @staticmethod
    def unparsed_text_available(href, *, encoding=UNSET) -> Expr:
        """Build a native XQuery expression.

        Returns true if a call to unparsed-text would succeed with identical arguments.

        Parameters
        ----------
        href : xs:string
            The $href is a string containing a URI reference. It must identify a
            resource that can be read as text. If the URI is a relative URI then it is
            resolved relative to the base URI from the static context.
        encoding : xs:string
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
        Expr
            Composable call to ``fn:unparsed-text-available``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:unparsed-text-available
        """
        return _optional_call("fn:unparsed-text-available", href, encoding)

    @staticmethod
    def upper_case(string) -> Expr:
        """Build a native XQuery expression.

        Returns the specified string converting all of the characters to upper-case
        characters.

        Parameters
        ----------
        string : xs:string?
            The string to upper-case.

        Returns
        -------
        Expr
            Composable call to ``fn:upper-case``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:upper-case
        """
        return _FunctionCall("fn:upper-case", (string,))

    @staticmethod
    def year_from_date(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:integer representing the year component in the localized value of
        $arg.

        Parameters
        ----------
        arg : xs:date?
            The date whose year component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:year-from-date``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:year-from-date
        """
        return _FunctionCall("fn:year-from-date", (arg,))

    @staticmethod
    def year_from_date_time(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:integer representing the year component in the localized value of
        $arg.

        Parameters
        ----------
        arg : xs:dateTime?
            The dateTime whose year component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:year-from-dateTime``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:year-from-dateTime
        """
        return _FunctionCall("fn:year-from-dateTime", (arg,))

    @staticmethod
    def years_from_duration(arg) -> Expr:
        """Build a native XQuery expression.

        Returns an xs:integer representing the years component in the canonical lexical
        representation of the value of $arg.

        Parameters
        ----------
        arg : xs:duration?
            The duration whose year component will be returned.

        Returns
        -------
        Expr
            Composable call to ``fn:years-from-duration``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:years-from-duration
        """
        return _FunctionCall("fn:years-from-duration", (arg,))

    @staticmethod
    def zero_or_one(arg) -> Expr:
        """Build a native XQuery expression.

        Returns $arg if it contains zero or one items.

        Parameters
        ----------
        arg : item()*
            The sequence of items.

        Returns
        -------
        Expr
            Composable call to ``fn:zero-or-one``.

        Notes
        -----
        Native reference: https://docs.marklogic.com/fn:zero-or-one
        """
        return _FunctionCall("fn:zero-or-one", (arg,))
