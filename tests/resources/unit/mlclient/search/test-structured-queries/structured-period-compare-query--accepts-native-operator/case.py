from mlclient.search.structured import PeriodCompareQuery


def run():
    PeriodCompareQuery("system", "iso_equals", "valid")
