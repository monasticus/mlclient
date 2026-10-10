from mlclient.search.structured import RangeQuery
from datetime import datetime
from mlclient.search.structured import Field


def run():
    return RangeQuery(Field("price"), datetime(2026, 1, 2, 3, 4, 5))
