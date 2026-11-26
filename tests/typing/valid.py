"""Consumer contracts checked against the installed package."""

from __future__ import annotations

from collections.abc import Hashable
from xml.etree.ElementTree import Element

from typing_extensions import assert_type

from mlclient import AsyncMLClient, MLClient, MLClientManager
from mlclient.models.results import ParsedValue
from mlclient.search.options import NativeOption, NativeOptions, SearchOptions
from mlclient.services import AsyncCtsService, CtsService
from mlclient.xquery import FunctionCall, ModuleFunctionCall, fn


def consume(client: MLClient, manager: MLClientManager) -> None:
    with client as connected:
        assert_type(connected, MLClient)
        assert_type(connected.eval.xquery("1"), ParsedValue)
        assert_type(connected.eval.xquery("1", output_type=str), str | list[str])
        assert_type(connected.eval.xquery("1", output_type=bytes), bytes | list[bytes])
        assert_type(
            connected.invoke.module("/example.xqy", output_type=str),
            str | list[str],
        )
        cts = CtsService(connected.rest)
        assert_type(cts.uris(), list[str])
        assert_type(cts.uris(output_type=bytes), list[bytes])
        assert_type(cts.uri_match("*.xml", output_type=str), list[str])
        assert_type(cts.uri_match("*.xml", output_type=bytes), list[bytes])
        cts.word_query("coffee")
    manager.get_config("content", retry=0, timeout=None)
    manager.get_client("content", limits=5)
    MLClient(retry=2, limits=10)
    AsyncMLClient(retry=0)


async def consume_async(client: AsyncMLClient) -> None:
    async with client as connected:
        assert_type(connected, AsyncMLClient)
        assert_type(await connected.eval.xquery("1", output_type=str), str | list[str])
        cts = AsyncCtsService(connected.rest)
        assert_type(await cts.uris(), list[str])
        assert_type(await cts.uris(output_type=bytes), list[bytes])
        assert_type(await cts.uri_match("*.xml"), list[str])
        assert_type(await cts.uri_match("*.xml", output_type=bytes), list[bytes])
        cts.word_query("coffee")


def collections(strings: list[str], nodes: list[Element]) -> None:
    assert_type(fn.count(strings), FunctionCall)
    assert_type(fn.base_uri(nodes), FunctionCall)
    ModuleFunctionCall(
        "example",
        strings,
        namespace="https://example.com",
        module_path="/example.xqy",
    )


def hashable_options(
    options: SearchOptions,
    native: NativeOption,
    group: NativeOptions,
) -> tuple[Hashable, Hashable, Hashable]:
    return options, native, group
