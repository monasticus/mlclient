"""Native ``cts:period-range-query`` serialization through the public CTS builder."""

from mlclient.xquery import cts


def run():
    return cts.period_range_query("valid", "aln_before")
