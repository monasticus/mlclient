from datetime import datetime
from mlclient.functions.xqy import cts


def run():
    return cts.lsqt_query(
        "temporal",
        timestamp=datetime(2026, 1, 2, 3, 4, 5),
        options="checked",
        weight=2.5,
    ).compile()
