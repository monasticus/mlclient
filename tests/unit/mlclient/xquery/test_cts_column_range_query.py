"""Public compilation and native serialization of ColumnRangeQuery."""

from xml.etree.ElementTree import tostring

import pytest

from mlclient.xquery import ColumnRangeQuery, cts


def test_compilation():
    query = cts.column_range_query(
        "reports",
        "items",
        "price",
        2,
        operator=">=",
        options="cached",
        weight=2,
    )
    assert isinstance(query, ColumnRangeQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:string exte'
            "rnal;\ndeclare variable $v1 as xs:string external;\ndeclare vari"
            "able $v2 as xs:string external;\ndeclare variable $v3 as xs:inte"
            "ger external;\ndeclare variable $v4 as xs:string external;\ndecl"
            "are variable $v5 as xs:string external;\ndeclare variable $v6 as"
            " xs:integer external;\ncts:column-range-query($v0, $v1, $v2, $v3"
            ", xs:string($v4), $v5, xs:double($v6))"
        ),
        {
            "v0": "reports",
            "v1": "items",
            "v2": "price",
            "v3": "2",
            "v4": ">=",
            "v5": "cached",
            "v6": "2",
        },
    )


def test_serialization_requires_tde_column_metadata():
    query = cts.column_range_query("reports", "items", "price", 2)
    message = (
        "cts:column-range-query: CTS column serialization requires the "
        "destination database's TDE column ID; use with_column_id()."
    )
    with pytest.raises(TypeError) as error:
        query.serialize()
    assert str(error.value) == message
    with pytest.raises(TypeError) as error:
        query.to_xml()
    assert str(error.value) == message


def test_serialization_with_explicit_column_id():
    original = cts.column_range_query(
        "reports", "items", "price", 2, operator=">=", options="cached", weight=2,
    )
    query = original.with_column_id(11548423394257569743)
    assert query.compile() == original.compile()
    assert original.column_id is None
    expected = {
        "tripleRangeQuery": {
            "objectOperator": ">=",
            "predicate": [
                {"column": "reports.items.price", "columnID": "11548423394257569743"},
            ],
            "object": [
                {"datatype": "http://www.w3.org/2001/XMLSchema#integer", "value": 2},
            ],
            "options": ["cached"],
            "weight": 2,
        },
    }
    assert query.serialize() == expected
    assert query.to_combined_query() == {"search": {"ctsquery": expected}}
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:triple-range-query xmlns:cts="http://marklogic.com/cts" '
        'object-operator="&gt;=" weight="2"><cts:predicate '
        'column="reports.items.price" '
        'columnID="11548423394257569743" /><cts:object '
        'datatype="http://www.w3.org/2001/XMLSchema#integer">2</cts:object>'
        "<cts:option>cached</cts:option></cts:triple-range-query>"
    )


def test_invalid_column_id():
    query = cts.column_range_query("reports", "items", "price", 2)
    with pytest.raises(ValueError, match="CTS column ID must be") as error:
        query.with_column_id(-1)
    assert str(error.value) == "CTS column ID must be an unsigned 64-bit integer."
