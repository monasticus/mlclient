"""Test QtextQuery through its public API."""

from mlclient.search.structured import QtextQuery


def run():
    return QtextQuery("blue AND green")
