import json
from mlclient.xquery import fn


def run():
    (_code, variables) = fn.count([{"items": [1, None, True]}, {"items": []}]).compile()
    assert (
        "fn:count((xdmp:unquote($v0) ! node(), xdmp:unquote($v2) ! node()))"
        in variables.values()
    )
    assert json.loads(variables["v0"]) == {"items": [1, None, True]}
    assert json.loads(variables["v2"]) == {"items": []}
    assert fn.count(({"items": []},)).compile()[1]["v0"] == '{"items": []}'
