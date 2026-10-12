import json
import sys
from xml.etree.ElementTree import ElementTree, fromstring

import pytest

from mlclient.xquery import Cts, FunctionCall, XqyExpression, fn


def test_abstract_expression_requires_render():
    with pytest.raises(TypeError) as error:
        XqyExpression()
    expected_message = (
        ("Can't instantiate abstract class XqyExpression with abstract method render")
        if sys.version_info < (3, 12)
        else (
            "Can't instantiate abstract class XqyExpression without "
            "an implementation for abstract method 'render'"
        )
    )
    assert str(error.value) == expected_message


def test_expression_string_contains_complete_source():
    assert str(Cts.uris()) == 'xquery version "1.0-ml";\ncts:uris()'


def test_circular_json_is_rejected():
    value = {}
    value["self"] = value
    with pytest.raises(ValueError, match=r"^Circular reference detected") as error:
        fn.data(value)
    assert str(error.value) == "Circular reference detected"


def test_element_tail_is_not_part_of_the_input_node():
    element = fromstring("<report>blue</report>")
    element.tail = "outside"
    assert fn.data(element).compile()[1]["v0"] == "<report>blue</report>"
    assert element.tail == "outside"


@pytest.mark.parametrize(
    ("value", "error", "message"),
    [
        ({1: "blue"}, TypeError, "JSON object keys must be strings"),
        ({"nested": [{2: "blue"}]}, TypeError, "JSON object keys must be strings"),
        (
            {"value": float("nan")},
            ValueError,
            "Out of range float values are not JSON compliant"
            + (": nan" if sys.version_info >= (3, 12) else ""),
        ),
        (
            {"value": float("inf")},
            ValueError,
            "Out of range float values are not JSON compliant"
            + (": inf" if sys.version_info >= (3, 12) else ""),
        ),
        (
            {"value": object()},
            TypeError,
            "Object of type object is not JSON serializable",
        ),
        (ElementTree(), ValueError, "an XML document must have a root element"),
    ],
)
def test_invalid_python_nodes_fail_when_built(value, error, message):
    with pytest.raises(error) as caught:
        fn.data(value)
    assert str(caught.value) == message


def test_nested_json_arrays_remain_arrays():
    (_code, variables) = fn.count([{"items": [1, None, True]}, {"items": []}]).compile()
    assert (
        "fn:count((xdmp:unquote($v0) ! node(), xdmp:unquote($v2) ! node()))"
    ) in variables.values()
    assert json.loads(variables["v0"]) == {"items": [1, None, True]}
    assert json.loads(variables["v2"]) == {"items": []}
    assert fn.count(({"items": []},)).compile()[1]["v0"] == '{"items": []}'


def test_node_inputs_work_in_custom_calls():
    expression = FunctionCall("fn:node-kind", (fromstring("<report/>"),))
    assert "fn:node-kind(xdmp:unquote($v0) ! *)" in expression.compile()[1].values()
