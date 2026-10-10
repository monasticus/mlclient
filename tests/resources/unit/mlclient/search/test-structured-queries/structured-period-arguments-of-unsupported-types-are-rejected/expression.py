from datetime import datetime
from mlclient.search.structured import Period


def run():
    return Period(datetime(2026, 1, 1), 2027)
