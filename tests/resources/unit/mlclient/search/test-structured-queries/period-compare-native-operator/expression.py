from mlclient.search.structured import PeriodCompareQuery


def run():
    return PeriodCompareQuery("system", "iso_equals", "valid")
