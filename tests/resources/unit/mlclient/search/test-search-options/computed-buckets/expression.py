from mlclient.search import options as o
from mlclient.search import structured as s


def run():
    return o.SearchOptions(
        o.RangeConstraint(
            "created",
            o.Range(
                s.JsonProperty("created"),
                "xs:dateTime",
                computed_buckets=[
                    o.ComputedBucket(
                        "today",
                        "Today",
                        ge="P0D",
                        lt="P1D",
                        anchor="start-of-day",
                        ge_anchor="start-of-day",
                        lt_anchor="start-of-day",
                    ),
                ],
            ),
        ),
    )
