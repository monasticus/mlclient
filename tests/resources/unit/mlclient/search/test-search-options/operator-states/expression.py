from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.Operator(
            "sort",
            [
                o.OperatorState(
                    "recent",
                    o.SearchOptions(
                        o.SortOrder(
                            o.Range(s.JsonProperty("created"), "xs:dateTime"),
                            direction="descending",
                        ),
                        o.PageLength(10),
                        o.Forest(123),
                        o.Forest("456"),
                        o.SearchOptionString("unfiltered"),
                    ),
                ),
                o.OperatorState(
                    "relevance",
                    o.SearchOptions(
                        o.SortOrder("score", direction="descending"),
                        o.QualityWeight(1),
                    ),
                ),
            ],
        ),
    )
