"""Test DocumentQuery through the public structured-query API."""

from mlclient.search.structured import DocumentQuery


def run():
    return DocumentQuery(["/reports/first.xml", "/reports/second.json"])
