from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.Values(
            "prices",
            o.Range(s.JsonProperty("price"), "xs:decimal"),
            style="consistent",
            aggregates=[o.Aggregate("sum"), o.Aggregate("median", "stats")],
            options=["item-frequency", "descending"],
            annotation="Prices",
        ),
    )
