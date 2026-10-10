from mlclient.search.structured import PeriodRangeQuery


def run():
    return PeriodRangeQuery("valid", "aln_equals", "2024")
