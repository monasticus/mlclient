from mlclient.search.structured import QtextQuery, Query


def run():
    return Query(QtextQuery("blue AND green"))
