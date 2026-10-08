from xml.etree import ElementTree

import pytest

from mlclient.search.structured import RangeConstraintQuery


def test_serializes_to_json():
    query = RangeConstraintQuery("price", [3, 4], operator="EQ", options=["cached"])
    expected = {
        "range-constraint-query": {
            "constraint-name": "price",
            "value": ["3", "4"],
            "range-operator": "EQ",
            "range-option": "cached",
        },
    }
    assert query.serialize() == expected
    assert query.serialize("json") == expected


def test_serializes_to_xml():
    query = RangeConstraintQuery("price", [3, 4], operator="EQ", options=["cached"])
    expected = ElementTree.fromstring(
        '<range-constraint-query xmlns="http://marklogic.com/appservices/search">'
        "<constraint-name>price</constraint-name><value>3</value><value>4</value>"
        "<range-operator>EQ</range-operator><range-option>cached</range-option>"
        "</range-constraint-query>",
    )
    assert ElementTree.tostring(query.to_xml()) == ElementTree.tostring(expected)


def test_invalid_operator():
    with pytest.raises(ValueError, match=r".+") as exc:
        RangeConstraintQuery("price", 3, operator="INVALID").serialize("xml")
    assert str(exc.value) == "Range operator must be LT, LE, GT, GE, EQ, or NE."


def test_empty_values():
    with pytest.raises(ValueError, match=r".+") as exc:
        RangeConstraintQuery("price", []).serialize("xml")
    assert str(exc.value) == "Range queries require at least one value."


def test_multiple_relational_values():
    with pytest.raises(ValueError, match=r".+") as exc:
        RangeConstraintQuery("price", [3, 4], operator="GT").serialize("xml")
    assert str(exc.value) == "Multiple range values require EQ or NE."
