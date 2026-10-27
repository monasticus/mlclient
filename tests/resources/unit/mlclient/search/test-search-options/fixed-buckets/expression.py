from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.RangeConstraint(
            "price",
            o.Range(
                s.JsonProperty("price"),
                "xs:decimal",
                fragment_scope="documents",
                weight=2,
                options=["cached"],
                buckets=[
                    o.Bucket("low", "Under ten", ge="0", lt="10"),
                    o.Bucket("high", "Ten or more", ge="10"),
                ],
            ),
            options=["limit=5"],
            annotation="Prices",
        ),
    )
