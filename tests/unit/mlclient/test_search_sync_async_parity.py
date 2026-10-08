"""Async search classes mirror their sync counterparts' signatures and docs."""

from __future__ import annotations

import inspect
import re

import pytest

from mlclient.api.search import AsyncSearchApi, SearchApi
from mlclient.api.values import AsyncValuesApi, ValuesApi
from mlclient.services.search import AsyncSearchService, SearchService

PAIRS = [
    (SearchService, AsyncSearchService),
    (SearchApi, AsyncSearchApi),
    (ValuesApi, AsyncValuesApi),
]


@pytest.mark.parametrize(("sync_class", "async_class"), PAIRS)
def test_async_class_has_the_same_methods(sync_class, async_class):
    assert _methods(async_class).keys() == _methods(sync_class).keys()


@pytest.mark.parametrize(("sync_class", "async_class"), PAIRS)
def test_async_methods_have_the_same_parameters(sync_class, async_class):
    async_methods = _methods(async_class)
    for name, sync_method in _methods(sync_class).items():
        sync_parameters = inspect.signature(sync_method).parameters
        async_parameters = inspect.signature(async_methods[name]).parameters
        assert [_without_async(str(p)) for p in async_parameters.values()] == [
            str(p) for p in sync_parameters.values()
        ], name


@pytest.mark.parametrize(("sync_class", "async_class"), PAIRS)
def test_async_methods_have_the_same_docs(sync_class, async_class):
    async_methods = _methods(async_class)
    for name, sync_method in _methods(sync_class).items():
        async_doc = _without_async(inspect.getdoc(async_methods[name]))
        assert async_doc == inspect.getdoc(sync_method), name


def _methods(cls: type) -> dict:
    return {
        name: member.fget if isinstance(member, property) else member
        for name, member in vars(cls).items()
        if callable(member) or isinstance(member, property)
    }


def _without_async(text: str) -> str:
    return re.sub(r"\bAsync(?=[A-Z])", "", text)
