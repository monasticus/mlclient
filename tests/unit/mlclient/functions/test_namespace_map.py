import pytest

from mlclient.functions.xqy import Cts, fn


@pytest.mark.parametrize(
    ("bindings", "expected_code", "expected_variables"),
    [
        (
            {},
            (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:string external;\n"
                "cts:path-reference($v0, (), map:new(()))"
            ),
            {"v0": "/item"},
        ),
        (
            {"p": "https://monasticus.com/mlclient/examples/p"},
            (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:string external;\n"
                "declare variable $v1 as xs:string external;\n"
                "declare variable $v2 as xs:string external;\n"
                "cts:path-reference($v0, (), map:entry($v1, $v2))"
            ),
            {
                "v0": "/item",
                "v1": "p",
                "v2": "https://monasticus.com/mlclient/examples/p",
            },
        ),
        (
            {
                "p": "https://monasticus.com/mlclient/examples/p",
                "q": "https://monasticus.com/mlclient/examples/q",
            },
            (
                'xquery version "1.0-ml";\n'
                "declare variable $v0 as xs:string external;\n"
                "declare variable $v1 as xs:string external;\n"
                "declare variable $v2 as xs:string external;\n"
                "declare variable $v3 as xs:string external;\n"
                "declare variable $v4 as xs:string external;\n"
                "cts:path-reference($v0, (), map:new((map:entry($v1, $v2), "
                "map:entry($v3, $v4))))"
            ),
            {
                "v0": "/item",
                "v1": "p",
                "v2": "https://monasticus.com/mlclient/examples/p",
                "v3": "q",
                "v4": "https://monasticus.com/mlclient/examples/q",
            },
        ),
    ],
)
def test_reference_namespace_map(bindings, expected_code, expected_variables):
    code, variables = Cts.path_reference("/item", namespaces=bindings).compile()

    assert code == expected_code
    assert variables == expected_variables


def test_reference_namespace_map_snapshot():
    bindings = {"p": "https://monasticus.com/mlclient/examples/local"}
    expression = Cts.path_reference("/p:item", namespaces=bindings)
    bindings["p"] = "changed"

    code, variables = expression.compile(
        namespaces={"p": "https://monasticus.com/mlclient/examples/global"},
    )

    assert code == (
        'xquery version "1.0-ml";\n'
        "declare namespace p = "
        '"https://monasticus.com/mlclient/examples/global";\n'
        "declare variable $v0 as xs:string external;\n"
        "declare variable $v1 as xs:string external;\n"
        "declare variable $v2 as xs:string external;\n"
        "cts:path-reference($v0, (), map:entry($v1, $v2))"
    )
    assert variables == {
        "v0": "/p:item",
        "v1": "p",
        "v2": "https://monasticus.com/mlclient/examples/local",
    }


def test_reference_namespace_expression_is_preserved():
    expression = Cts.path_reference("/item", namespaces=fn.true())
    code, variables = expression.compile()

    assert code == (
        'xquery version "1.0-ml";\n'
        "declare variable $v0 as xs:string external;\n"
        "cts:path-reference($v0, (), fn:true())"
    )
    assert variables == {"v0": "/item"}
