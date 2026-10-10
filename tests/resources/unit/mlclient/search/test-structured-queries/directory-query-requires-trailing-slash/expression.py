"""Test DirectoryQuery through the public structured-query API."""

from mlclient.search.structured import DirectoryQuery


def run():
    return DirectoryQuery("/reports")
