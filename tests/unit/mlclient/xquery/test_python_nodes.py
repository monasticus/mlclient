"""Python node inputs through public XQuery builders and serializers."""

import json
from xml.etree.ElementTree import (
    Comment, ElementTree, ProcessingInstruction, SubElement, fromstring, tostring,
)

import pytest

from mlclient.xquery import FunctionCall, SimilarQuery, ReverseQuery, cts, fn, xdmp, xs


NODE_BUILDERS = [
    pytest.param(fn.base_uri, id="fn.base_uri.arg"),
    pytest.param(fn.boolean, id="fn.boolean.arg"),
    pytest.param(fn.count, id="fn.count.sequence"),
    pytest.param(fn.data, id="fn.data.arg"),
    pytest.param(
        lambda node: fn.deep_equal(node, fn.string("auxiliary")),
        id="fn.deep_equal.parameter1",
    ),
    pytest.param(
        lambda node: fn.deep_equal(fn.string("auxiliary"), node),
        id="fn.deep_equal.parameter2",
    ),
    pytest.param(fn.distinct_nodes, id="fn.distinct_nodes.nodes"),
    pytest.param(fn.distinct_values, id="fn.distinct_values.arg"),
    pytest.param(
        lambda node: fn.document(fn.string("auxiliary"), base_node=node),
        id="fn.document.base_node",
    ),
    pytest.param(fn.document_uri, id="fn.document_uri.arg"),
    pytest.param(fn.empty, id="fn.empty.sequence"),
    pytest.param(lambda node: fn.error(data=node), id="fn.error.data"),
    pytest.param(fn.exactly_one, id="fn.exactly_one.arg"),
    pytest.param(fn.exists, id="fn.exists.sequence"),
    pytest.param(
        lambda node: fn.filter(fn.string("auxiliary"), node),
        id="fn.filter.seq",
    ),
    pytest.param(
        lambda node: fn.fold_left(fn.string("auxiliary"), node, fn.string("auxiliary")),
        id="fn.fold_left.zero",
    ),
    pytest.param(
        lambda node: fn.fold_left(fn.string("auxiliary"), fn.string("auxiliary"), node),
        id="fn.fold_left.seq",
    ),
    pytest.param(
        lambda node: fn.fold_right(
            fn.string("auxiliary"),
            node,
            fn.string("auxiliary"),
        ),
        id="fn.fold_right.zero",
    ),
    pytest.param(
        lambda node: fn.fold_right(
            fn.string("auxiliary"),
            fn.string("auxiliary"),
            node,
        ),
        id="fn.fold_right.seq",
    ),
    pytest.param(fn.generate_id, id="fn.generate_id.node"),
    pytest.param(fn.head, id="fn.head.seq"),
    pytest.param(
        lambda node: fn.id(fn.string("auxiliary"), node=node),
        id="fn.id.node",
    ),
    pytest.param(
        lambda node: fn.idref(fn.string("auxiliary"), node=node),
        id="fn.idref.node",
    ),
    pytest.param(
        fn.in_scope_prefixes,
        id="fn.in_scope_prefixes.element",
    ),
    pytest.param(
        lambda node: fn.insert_before(
            node,
            fn.string("auxiliary"),
            fn.string("auxiliary"),
        ),
        id="fn.insert_before.target",
    ),
    pytest.param(
        lambda node: fn.insert_before(
            fn.string("auxiliary"),
            fn.string("auxiliary"),
            node,
        ),
        id="fn.insert_before.inserts",
    ),
    pytest.param(
        lambda node: fn.key(fn.string("auxiliary"), fn.string("auxiliary"), top=node),
        id="fn.key.top",
    ),
    pytest.param(
        lambda node: fn.lang(fn.string("auxiliary"), node=node),
        id="fn.lang.node",
    ),
    pytest.param(fn.local_name, id="fn.local_name.arg"),
    pytest.param(lambda node: fn.map(fn.string("auxiliary"), node), id="fn.map.seq"),
    pytest.param(
        lambda node: fn.map_pairs(fn.string("auxiliary"), node, fn.string("auxiliary")),
        id="fn.map_pairs.seq1",
    ),
    pytest.param(
        lambda node: fn.map_pairs(fn.string("auxiliary"), fn.string("auxiliary"), node),
        id="fn.map_pairs.seq2",
    ),
    pytest.param(fn.name, id="fn.name.arg"),
    pytest.param(fn.namespace_uri, id="fn.namespace_uri.arg"),
    pytest.param(
        lambda node: fn.namespace_uri_for_prefix(fn.string("auxiliary"), node),
        id="fn.namespace_uri_for_prefix.element",
    ),
    pytest.param(fn.nilled, id="fn.nilled.arg"),
    pytest.param(fn.node_kind, id="fn.node_kind.node"),
    pytest.param(fn.node_name, id="fn.node_name.arg"),
    pytest.param(fn.not_, id="fn.not_.arg"),
    pytest.param(fn.one_or_more, id="fn.one_or_more.arg"),
    pytest.param(
        lambda node: fn.remove(node, fn.string("auxiliary")),
        id="fn.remove.target",
    ),
    pytest.param(
        lambda node: fn.resolve_qname(fn.string("auxiliary"), node),
        id="fn.resolve_qname.element",
    ),
    pytest.param(fn.reverse, id="fn.reverse.target"),
    pytest.param(fn.root, id="fn.root.arg"),
    pytest.param(fn.string, id="fn.string.arg"),
    pytest.param(
        lambda node: fn.subsequence(node, fn.string("auxiliary")),
        id="fn.subsequence.source_seq",
    ),
    pytest.param(fn.tail, id="fn.tail.seq"),
    pytest.param(
        lambda node: fn.trace(node, fn.string("auxiliary")),
        id="fn.trace.value",
    ),
    pytest.param(fn.unordered, id="fn.unordered.source_seq"),
    pytest.param(fn.zero_or_one, id="fn.zero_or_one.arg"),
    pytest.param(
        lambda node: cts.classify(node, fn.string("auxiliary")),
        id="cts.classify.data_nodes",
    ),
    pytest.param(
        lambda node: cts.classify(fn.string("auxiliary"), node),
        id="cts.classify.classifier",
    ),
    pytest.param(
        lambda node: cts.classify(
            fn.string("auxiliary"),
            fn.string("auxiliary"),
            options=node,
        ),
        id="cts.classify.options",
    ),
    pytest.param(
        lambda node: cts.classify(
            fn.string("auxiliary"),
            fn.string("auxiliary"),
            training_nodes=node,
        ),
        id="cts.classify.training_nodes",
    ),
    pytest.param(cts.cluster, id="cts.cluster.nodes"),
    pytest.param(
        lambda node: cts.cluster(fn.string("auxiliary"), options=node),
        id="cts.cluster.options",
    ),
    pytest.param(lambda node: cts.confidence(node=node), id="cts.confidence.node"),
    pytest.param(
        lambda node: cts.contains(node, cts.true_query()),
        id="cts.contains.nodes",
    ),
    pytest.param(
        cts.distinctive_terms,
        id="cts.distinctive_terms.nodes",
    ),
    pytest.param(
        lambda node: cts.distinctive_terms(fn.string("auxiliary"), options=node),
        id="cts.distinctive_terms.options",
    ),
    pytest.param(
        lambda node: cts.element_walk(
            node,
            fn.string("auxiliary"),
            fn.string("auxiliary"),
        ),
        id="cts.element_walk.node",
    ),
    pytest.param(
        cts.entity_dictionary,
        id="cts.entity_dictionary.entities",
    ),
    pytest.param(
        lambda node: cts.entity_highlight(node, fn.string("auxiliary")),
        id="cts.entity_highlight.node",
    ),
    pytest.param(
        lambda node: cts.entity_walk(node, fn.string("auxiliary")),
        id="cts.entity_walk.node",
    ),
    pytest.param(lambda node: cts.fitness(node=node), id="cts.fitness.node"),
    pytest.param(
        lambda node: cts.highlight(node, cts.true_query(), fn.string("auxiliary")),
        id="cts.highlight.node",
    ),
    pytest.param(
        lambda node: cts.parse(cts.true_query(), bindings=node),
        id="cts.parse.bindings",
    ),
    pytest.param(lambda node: cts.quality(node=node), id="cts.quality.node"),
    pytest.param(cts.query, id="cts.query.query"),
    pytest.param(
        cts.reference_parse,
        id="cts.reference_parse.reference",
    ),
    pytest.param(
        lambda node: cts.relevance_info(node=node),
        id="cts.relevance_info.node",
    ),
    pytest.param(lambda node: cts.remainder(node=node), id="cts.remainder.node"),
    pytest.param(cts.reverse_query, id="cts.reverse_query.nodes"),
    pytest.param(lambda node: cts.score(node=node), id="cts.score.node"),
    pytest.param(cts.similar_query, id="cts.similar_query.nodes"),
    pytest.param(
        lambda node: cts.similar_query(fn.string("auxiliary"), options=node),
        id="cts.similar_query.options",
    ),
    pytest.param(
        lambda node: cts.train(node, fn.string("auxiliary")),
        id="cts.train.training_nodes",
    ),
    pytest.param(
        lambda node: cts.train(fn.string("auxiliary"), node),
        id="cts.train.labels",
    ),
    pytest.param(
        lambda node: cts.train(
            fn.string("auxiliary"),
            fn.string("auxiliary"),
            options=node,
        ),
        id="cts.train.options",
    ),
    pytest.param(
        lambda node: cts.walk(node, cts.true_query(), fn.string("auxiliary")),
        id="cts.walk.node",
    ),
    pytest.param(xs.date, id="xs.date"),
    pytest.param(xs.date_time, id="xs.date_time"),
    pytest.param(xs.decimal, id="xs.decimal"),
    pytest.param(xs.double, id="xs.double"),
    pytest.param(xs.integer, id="xs.integer"),
    pytest.param(xs.qname, id="xs.qname"),
    pytest.param(xs.string, id="xs.string"),
    pytest.param(xdmp.unquote, id="xdmp.unquote"),
]


@pytest.mark.parametrize("builder", NODE_BUILDERS)
@pytest.mark.parametrize("kind", ["json", "element", "document"])
def test_python_nodes_are_bound_and_snapshotted(builder, kind):
    if kind == "json":
        node = {"label": "blue", "nested": [{"count": 2}]}
        expected = xdmp.unquote(json.dumps(node)).xpath("node()")
    else:
        element = fromstring('<report xmlns="urn:reports">blue</report>')
        node = element if kind == "element" else ElementTree(element)
        expected = xdmp.unquote(
            tostring(element, encoding="unicode").replace("ns0", "node0"),
        )
        if kind == "element":
            expected = expected.xpath("*")
    expression = builder(node)
    original = expression.compile()
    assert original == builder(expected).compile()
    assert "blue" not in original[0]
    assert any("blue" in str(value) for value in original[1].values())
    if kind == "json":
        node["nested"][0]["count"] = 99
    else:
        element.text = "changed"
    assert expression.compile() == original


@pytest.mark.parametrize(
    "constructor",
    [cts.similar_query, cts.reverse_query, SimilarQuery, ReverseQuery],
)
def test_cts_models_accept_python_nodes_and_sequences(constructor):
    element = fromstring("<report>blue</report>")
    models = [{"label": "blue"}, element, ElementTree(element)]
    query = constructor(models)
    key = (
        "similarQuery"
        if constructor in (cts.similar_query, SimilarQuery)
        else "reverseQuery"
    )
    assert query.to_json() == {
        key: {
            "nodes": [
                {"label": "blue"},
                "<report>blue</report>",
                "<report>blue</report>",
            ],
        },
    }
    assert "<report>blue</report>" in tostring(query.to_xml(), encoding="unicode")
    models[0]["label"] = "changed"
    element.text = "changed"
    assert query.to_json()[key]["nodes"][0] == {"label": "blue"}
    assert query.to_json()[key]["nodes"][1] == "<report>blue</report>"


def test_python_options_element_serializes_locally():
    options = fromstring(
        '<options xmlns="cts:distinctive-terms"><max-terms>20</max-terms></options>',
    )
    assert cts.similar_query({"label": "blue"}, options=options).to_json() == {
        "similarQuery": {"nodes": [{"label": "blue"}], "options": {"maxTerms": 20}},
    }


def test_lists_remain_sequences_and_nested_json_arrays_remain_arrays():
    _code, variables = fn.count([{"items": [1, None, True]}, {"items": []}]).compile()
    assert (
        "fn:count((xdmp:unquote($v0) ! node(), xdmp:unquote($v2) ! node()))"
        in variables.values()
    )
    assert json.loads(variables["v0"]) == {"items": [1, None, True]}
    assert json.loads(variables["v2"]) == {"items": []}
    assert fn.count(({"items": []},)).compile()[1]["v0"] == '{"items": []}'


@pytest.mark.parametrize(
    ("value", "error"),
    [
        ({1: "blue"}, TypeError),
        ({"nested": [{2: "blue"}]}, TypeError),
        ({"value": float("nan")}, ValueError),
        ({"value": float("inf")}, ValueError),
        ({"value": object()}, TypeError),
        (ElementTree(), ValueError),
    ],
)
def test_invalid_python_nodes_fail_when_built(value, error):
    with pytest.raises(error):
        fn.data(value)


def test_circular_json_is_rejected():
    value = {}
    value["self"] = value
    with pytest.raises(ValueError, match="Circular"):
        fn.data(value)


def test_element_tail_is_not_part_of_the_input_node():
    element = fromstring("<report>blue</report>")
    element.tail = "outside"
    assert fn.data(element).compile()[1]["v0"] == "<report>blue</report>"
    assert element.tail == "outside"


def test_node_inputs_also_work_in_custom_calls():
    expression = FunctionCall("fn:node-kind", (fromstring("<report/>"),))
    assert "fn:node-kind(xdmp:unquote($v0) ! *)" in expression.compile()[1].values()


def test_python_xml_namespaces_attributes_comments_and_tail():
    root = fromstring(
        '<r:report xmlns:r="urn:reports" xmlns:a="urn:attributes" '
        'a:flag="yes">blue</r:report>',
    )
    root.set("xmlns:node0", "urn:existing-prefix")
    root.append(Comment("retained"))
    root.append(ProcessingInstruction("status", "ready"))
    SubElement(root, "{urn:reports}label").text = "ns0:literal text"
    query = cts.similar_query(root)
    serialized = query.to_xml()
    model = serialized.find("{http://marklogic.com/cts}node")[0]
    assert model.tag == "{urn:reports}report"
    assert model.attrib["{urn:attributes}flag"] == "yes"
    assert model.find("{urn:reports}label").text == "ns0:literal text"
    assert "<!--retained-->" in tostring(serialized, encoding="unicode")
    assert "<?status ready?>" in tostring(serialized, encoding="unicode")
