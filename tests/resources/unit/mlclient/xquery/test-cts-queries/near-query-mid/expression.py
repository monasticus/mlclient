"""Native proximity query serialization and compilation."""

from mlclient.xquery import cts


def run():
    return cts.near_query(
        [cts.true_query(), cts.false_query()],
        options=["ordered", "minimum-distance=2"],
    )
