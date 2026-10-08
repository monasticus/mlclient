"""Public compilation and native serialization of RangeQuery."""

from xml.etree.ElementTree import tostring


import pytest

from mlclient.xquery import FunctionCall, RangeQuery, cts, fn


def test_unknown_reference_requires_evaluation():
    with pytest.raises(TypeError) as error:
        cts.range_query(fn.doc("/reference.xml"), "=", 2).serialize()
    assert str(error.value) == (
        "cts:range-query: reference: CTS reference argument requires server "
        "evaluation, got fn:doc('/reference.xml')."
    )


def test_unknown_reference_constructor_requires_evaluation():
    with pytest.raises(TypeError) as error:
        cts.range_query(
            FunctionCall("cts:reference-parse", ("reference",)),
            "=",
            2,
        ).serialize()
    assert str(error.value) == (
        "cts:range-query: reference: CTS reference argument requires server "
        "evaluation, got cts:reference-parse('reference')."
    )


def test_reference_type_requires_evaluation():
    with pytest.raises(TypeError) as error:
        cts.range_query(cts.element_reference("price"), "=", 2).serialize()
    assert str(error.value) == (
        "cts:range-query: reference: CTS reference scalarType requires an explicit "
        "option or server evaluation."
    )


def test_reference_projection_requires_evaluation():
    reference = cts.element_reference("price", options="type=int").pos(1)
    with pytest.raises(TypeError) as error:
        cts.range_query(reference, "=", 2).serialize()
    assert str(error.value) == (
        "cts:range-query: reference: CTS reference argument requires server "
        "evaluation, got Index(inner=FunctionCall(fn='cts:element-reference', "
        "args=(FunctionCall(fn='xs:QName', args=(AtomicValue(value='price', "
        "cast=None),), optionals=()),), optionals=(AtomicValue(value='type=int', "
        "cast=None),)), position=1)."
    )


def test_reference_unknown_option():
    with pytest.raises(
        ValueError,
        match="Unsupported local CTS reference option",
    ) as error:
        cts.range_query(
            cts.element_reference("price", options="unknown"),
            "=",
            2,
        ).serialize()
    assert str(error.value) == (
        "cts:range-query: reference: Unsupported local CTS reference option: unknown"
    )


def test_reference_namespace_maps_require_destination_context():
    query = cts.range_query(
        cts.path_reference(
            "/r:report/r:price",
            options="type=int",
            namespaces={"r": "urn:reports"},
        ),
        "=",
        2,
    )
    with pytest.raises(TypeError) as error:
        query.serialize()
    assert str(error.value) == (
        "cts:range-query: reference: CTS reference namespace maps cannot be "
        "serialized natively; use EQNames in the path or destination database "
        "namespaces."
    )


def test_reference_names_and_nullable_options_in_xml():
    query = cts.range_query(
        [
            cts.element_attribute_reference(
                fn.qname("urn:reports", "report"),
                "label",
                options=[
                    "type=string",
                    "collation=http://marklogic.com/collation/",
                    "nullable",
                ],
            ),
            cts.field_reference("price", options=["type=int", "non-nullable"]),
            cts.json_property_reference("price", options="type=int"),
            cts.path_reference("/report/price", options="type=int"),
            cts.uri_reference(),
            cts.collection_reference(),
            cts.iri_reference(),
        ],
        "=",
        "blue",
    )
    assert tostring(query.to_xml(), encoding="unicode") == (
        '<cts:range-query xmlns:cts="http://marklogic.com/cts" '
        'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" operator="=">'
        "<cts:element-attribute-reference><cts:parent-namespace-uri>urn:reports"
        "</cts:parent-namespace-uri><cts:parent-localname>report</cts:parent-localname>"
        "<cts:namespace-uri /><cts:localname>label</cts:localname>"
        "<cts:scalar-type>string</cts:scalar-type><cts:collation>"
        "http://marklogic.com/collation/</cts:collation><cts:nullable>true"
        "</cts:nullable></cts:element-attribute-reference><cts:field-reference>"
        "<cts:field-name>price</cts:field-name><cts:scalar-type>int</cts:scalar-type>"
        "<cts:nullable>false</cts:nullable></cts:field-reference>"
        "<cts:json-property-reference><cts:property>price</cts:property>"
        "<cts:scalar-type>int</cts:scalar-type></cts:json-property-reference>"
        "<cts:path-reference><cts:path-expression>/report/price</cts:path-expression>"
        "<cts:scalar-type>int</cts:scalar-type></cts:path-reference>"
        "<cts:uri-reference /><cts:collection-reference /><cts:iri-reference />"
        '<cts:value xmlns:xs="http://www.w3.org/2001/XMLSchema" '
        'xsi:type="xs:string">blue</cts:value></cts:range-query>'
    )


def test_reference_names_and_nullable_options_in_json():
    query = cts.range_query(
        [
            cts.field_reference("price", options=["type=int", "non-nullable"]),
            cts.json_property_reference("price", options="type=int"),
            cts.path_reference("/report/price", options="type=int"),
            cts.uri_reference(),
            cts.collection_reference(),
            cts.iri_reference(),
        ],
        "=",
        "blue",
    )
    assert query.to_json() == {
        "rangeQuery": {
            "reference": [
                {
                    "fieldReference": {
                        "fieldName": "price",
                        "scalarType": "int",
                        "nullable": False,
                    },
                },
                {"jsonPropertyReference": {"property": "price", "scalarType": "int"}},
                {
                    "pathReference": {
                        "pathExpression": "/report/price",
                        "scalarType": "int",
                    },
                },
                {"uriReference": {}},
                {"collectionReference": {}},
                {"iriReference": {}},
            ],
            "operator": "=",
            "value": [{"type": "string", "val": "blue"}],
        },
    }


def test_element_attribute_reference_does_not_serialize_to_json():
    query = cts.range_query(
        cts.element_attribute_reference("item", "amount", options="type=int"),
        "=",
        2,
    )

    with pytest.raises(TypeError) as error:
        query.to_json()

    assert str(error.value) == (
        "cts:range-query: reference: MarkLogic cannot read an element-attribute "
        "reference back from CTS JSON; serialize the query as XML or run it "
        "through eval"
    )


def test_compilation():
    query = cts.range_query(
        cts.element_reference("price", options=["type=int", "unchecked"]),
        ">=",
        [2, 3],
        options="cached",
        weight=2,
    )
    assert isinstance(query, RangeQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:string exte'
            "rnal;\ndeclare variable $v1 as xs:string external;\ndeclare vari"
            "able $v2 as xs:string external;\ndeclare variable $v3 as xs:stri"
            "ng external;\ndeclare variable $v4 as xs:integer external;\ndecl"
            "are variable $v5 as xs:integer external;\ndeclare variable $v6 a"
            "s xs:string external;\ndeclare variable $v7 as xs:integer extern"
            "al;\ncts:range-query(cts:element-reference(xs:QName($v0), ($v1, "
            "$v2)), xs:string($v3), ($v4, $v5), $v6, xs:double($v7))"
        ),
        {
            "v0": "price",
            "v1": "type=int",
            "v2": "unchecked",
            "v3": ">=",
            "v4": "2",
            "v5": "3",
            "v6": "cached",
            "v7": "2",
        },
    )


def test_serialization():
    query = cts.range_query(
        cts.element_reference("price", options=["type=int", "unchecked"]),
        ">=",
        [2, 3],
        options="cached",
        weight=2,
    )
    expected = {
        "rangeQuery": {
            "reference": [
                {
                    "elementReference": {
                        "namespaceURI": "",
                        "localname": "price",
                        "scalarType": "int",
                    },
                },
            ],
            "operator": ">=",
            "value": [{"type": "decimal", "val": "2"}, {"type": "decimal", "val": "3"}],
            "options": ["cached"],
            "weight": 2,
        },
    }
    assert query.serialize() == expected
    assert query.to_json() == expected
    assert query.to_combined_query() == {"search": {"ctsquery": expected}}
    assert tostring(query.serialize("xml"), encoding="unicode") == (
        '<cts:range-query xmlns:cts="http://marklogic.com/cts" xmlns:xsi='
        '"http://www.w3.org/2001/XMLSchema-instance" operator="&gt;=" wei'
        'ght="2"><cts:element-reference><cts:namespace-uri /><cts:localna'
        "me>price</cts:localname><cts:scalar-type>int</cts:scalar-type></"
        'cts:element-reference><cts:value xmlns:xs="http://www.w3.org/200'
        '1/XMLSchema" xsi:type="xs:integer">2</cts:value><cts:value xmlns'
        ':xs="http://www.w3.org/2001/XMLSchema" xsi:type="xs:integer">3</'
        "cts:value><cts:option>cached</cts:option></cts:range-query>"
    )
