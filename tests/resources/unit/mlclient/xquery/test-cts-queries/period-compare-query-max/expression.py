"""Native ``cts:period-compare-query`` serialization through the public CTS builder."""

from mlclient.xquery import cts


def run():
    return cts.period_compare_query(
        "system",
        "aln_equals",
        "valid",
        options="cached-incremental",
    )
