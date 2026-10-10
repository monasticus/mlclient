from mlclient.xquery import cts, xdmp


def run():
    query = cts.similar_query(xdmp.unquote('{"label":"blue","count":2}'))
    assert query.to_json() == {
        "similarQuery": {"nodes": [{"label": "blue", "count": 2}]},
    }
