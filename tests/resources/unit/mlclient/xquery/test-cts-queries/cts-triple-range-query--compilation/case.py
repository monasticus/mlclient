"""Public compilation and native serialization of TripleRangeQuery."""

from mlclient.xquery import FunctionCall, TripleRangeQuery, cts


def run():
    query = cts.triple_range_query(
        FunctionCall("sem:iri", ("urn:r",)),
        FunctionCall("sem:iri", ("urn:p",)),
        [2, True, "blue"],
        operator=">",
        options="cached",
        weight=2,
    )
    assert isinstance(query, TripleRangeQuery)
    assert query.compile() == (
        (
            'xquery version "1.0-ml";\ndeclare variable $v0 as xs:str'
            "ing external;\ndeclare variable $v1 as xs:string externa"
            "l;\ndeclare variable $v2 as xs:integer external;\ndeclare"
            " variable $v3 as xs:boolean external;\ndeclare variable "
            "$v4 as xs:string external;\ndeclare variable $v5 as xs:s"
            "tring external;\ndeclare variable $v6 as xs:string exter"
            "nal;\ndeclare variable $v7 as xs:integer external;\ncts:t"
            "riple-range-query(sem:iri($v0), sem:iri($v1), ($v2, $v3"
            ", $v4), $v5, $v6, xs:double($v7))"
        ),
        {
            "v0": "urn:r",
            "v1": "urn:p",
            "v2": "2",
            "v3": True,
            "v4": "blue",
            "v5": ">",
            "v6": "cached",
            "v7": "2",
        },
    )
