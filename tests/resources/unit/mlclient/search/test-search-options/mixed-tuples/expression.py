from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.Tuples(
            "uri-price",
            "uri",
            o.Range(s.JsonProperty("price"), "xs:decimal"),
            "collection",
            style="consistent",
            aggregates=[o.Aggregate("count")],
            options="item-frequency",
            annotation="Mixed indexes",
        ),
    )
