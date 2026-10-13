"""Native proximity query serialization and compilation."""

from mlclient.xquery import cts


def run():
    return cts.near_query(
        [cts.true_query(), cts.false_query()],
        distance=2.5,
        options=["ordered", "minimum-distance=2"],
        distance_weight=0.5,
    )
