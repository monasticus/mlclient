import pytest
import re
import sys

from mlclient.functions.xqy import XqyCompilationContext, fn


def test_compiler_bindings_are_independent_snapshots():
    context = XqyCompilationContext()
    context.bind("original")
    snapshot = context.variables
    snapshot["v0"] = "changed"
    snapshot["v1"] = "injected"

    assert context.variables == {"v0": "original"}


def test_compiler_bindings_property_is_read_only():
    context = XqyCompilationContext()

    with pytest.raises(AttributeError) as error:
        context.variables = {}

    expected_message = (
        "can't set attribute 'variables'"
        if sys.version_info < (3, 11)
        else "property 'variables' of 'XqyCompilationContext' object has no setter"
    )
    assert str(error.value) == expected_message


def test_compiler_assigns_successive_binding_names():
    context = XqyCompilationContext()

    assert context.bind("original") == "$v0"
    assert context.bind("next") == "$v1"
    assert context.variables == {"v0": "original", "v1": "next"}
    assert context.declarations == (
        "declare variable $v0 as xs:string external;\n"
        "declare variable $v1 as xs:string external;\n"
    )


@pytest.mark.parametrize(
    ("prefix", "message"),
    [
        ("fn", "empty or reserved namespace binding: 'fn'"),
        ("xs", "empty or reserved namespace binding: 'xs'"),
        ("cts", "empty or reserved namespace binding: 'cts'"),
        ("xdmp", "empty or reserved namespace binding: 'xdmp'"),
        ("map", "empty or reserved namespace binding: 'map'"),
        ("xml", "reserved namespace prefix: 'xml'"),
        ("xmlns", "reserved namespace prefix: 'xmlns'"),
    ],
)
def test_compiler_namespaces_cannot_be_rebound(prefix, message):
    with pytest.raises(ValueError, match=re.escape(message)) as error:
        fn.count([]).compile(
            namespaces={prefix: "https://monasticus.com/mlclient/examples/override"},
        )

    assert str(error.value) == message
