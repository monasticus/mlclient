"""Validate bundled knowledge routes, endpoint indexes and runnable templates."""

import asyncio
import inspect
import re
import runpy
from importlib.resources import files
from pathlib import Path

import httpx
import pytest
import respx
import yaml
from cleo.testers.command_tester import CommandTester

from mlclient import MLClient, MLClientManager
from mlclient.cli import MLCLIentApplication
from mlclient.functions.xqy import cts
from mlclient.models import Document, Metadata
from mlclient.services import AsyncDocumentsService, AsyncEvalService


def template(name):
    path = files("mlclient").joinpath("resources", "skills", "mlclient", "assets", name)
    return runpy.run_path(str(path))


@pytest.fixture
def skill(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: home)
    tester = CommandTester(MLCLIentApplication().find("install skill"))
    tester.execute("codex")
    return tmp_path / ".agents/skills/mlclient"


@pytest.fixture
def _environment(skill):
    directory = Path.cwd() / ".mlclient"
    directory.mkdir()
    (directory / "mlclient-test.yaml").write_text(
        "host: localhost\nauth: app\napp-servers:\n"
        "  - id: content\n    port: 8100\n    rest: true\n",
    )
    return skill


def test_skill_metadata_and_local_reference_links_are_complete(skill):
    text = (skill / "SKILL.md").read_text()
    metadata = yaml.safe_load(text.split("---", 2)[1])
    assert metadata["name"] == "mlclient"
    assert len(metadata["description"]) > 100
    for path in skill.rglob("*.md"):
        # Vendor export uses code-like Markdown links; validate our authored files.
        if path.name in {"v10.md", "v11.md", "v12.md"}:
            continue
        for target in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if not target.startswith(("https:", "http:", "#")):
                assert (path.parent / target.split("#")[0]).exists(), (path, target)


@pytest.mark.parametrize(("version", "count"), [(10, 392), (11, 401), (12, 406)])
def test_endpoint_index_preserves_each_full_contract_and_exact_ranges(
    skill, version, count,
):
    directory = skill / "references/endpoints"
    content = (directory / f"v{version}.md").read_text()
    headings = re.findall(
        r"^## (GET|HEAD|POST|PUT|PATCH|DELETE|OPTIONS) (.+)$", content, re.MULTILINE,
    )
    assert len(headings) == count
    lines = content.splitlines()
    rows = re.findall(
        r"^\| `([^`]+)` \| (.+) \| (\d+)-(\d+) \|$",
        (directory / f"v{version}-index.md").read_text(),
        re.MULTILINE,
    )
    assert len(rows) == count
    for endpoint, route, start, end in rows:
        section = "\n".join(lines[int(start) - 1 : int(end)])
        assert section.startswith("## " + endpoint.replace("&#124;", "|"))
        assert "### Summary" in section
        assert len(section) > 100
        assert route.startswith(("`ml.", "Raw HTTP"))
    assert "**Request Headers**" in content
    assert "**Response Headers**" in content
    assert "### Usage Notes" in content
    assert "### Example" in content


def test_every_indexed_python_wrapper_exists_with_recorded_signature(skill):
    text = (skill / "references/api-methods.md").read_text()
    entries = re.findall(r"## `(ml\.[^`]+)`.*?```python\n(.*?)\n```", text, re.DOTALL)
    assert len(entries) > 40
    ml = MLClient()
    for name, recorded in entries:
        value = ml
        for part in name.split(".")[1:]:
            value = getattr(value, part)
        signature = inspect.signature(value)
        assert "timeout" in signature.parameters
        assert recorded.startswith("self")
        for parameter in signature.parameters:
            assert re.search(r"\b" + parameter + r"\b", recorded)


@pytest.mark.usefixtures("_environment")
@pytest.mark.asyncio
async def test_concurrent_template_bounds_batches_and_preserves_order(
    mocker,
):
    evaluate = template("concurrent_eval.py")[
        "evaluate"
    ]
    active = 0
    peak = 0

    async def result(_service, _code, *, database):
        nonlocal active, peak
        active += 1
        peak = max(peak, active)
        await asyncio.sleep(0)
        active -= 1
        return database

    mocker.patch.object(AsyncEvalService, "file", autospec=True, side_effect=result)
    result = await evaluate(
        "test", "content", ["a", "b", "c", "d", "e"], "query.xqy", concurrency=2,
    )
    assert result == {key: key for key in ["a", "b", "c", "d", "e"]}
    assert peak == 2
    assert active == 0


@pytest.mark.usefixtures("_environment")
@pytest.mark.asyncio
async def test_concurrent_template_cancels_siblings_before_client_closure(
    mocker,
):
    evaluate = template("concurrent_eval.py")[
        "evaluate"
    ]
    cancelled = asyncio.Event()

    async def result(_service, _code, *, database):
        if database == "bad":
            await asyncio.sleep(0)
            message = "failed evaluation"
            raise RuntimeError(message)
        try:
            await asyncio.Event().wait()
        finally:
            cancelled.set()

    mocker.patch.object(AsyncEvalService, "file", autospec=True, side_effect=result)
    with pytest.raises(RuntimeError, match="failed evaluation"):
        await evaluate(
            "test", "content", ["bad", "waiting", "never"], "query.xqy", concurrency=2,
        )
    assert cancelled.is_set()


@pytest.mark.usefixtures("_environment")
@pytest.mark.asyncio
async def test_concurrent_template_rejects_invalid_concurrency():
    evaluate = template("concurrent_eval.py")[
        "evaluate"
    ]
    with pytest.raises(ValueError, match="positive"):
        await evaluate("test", "content", [], "query.xqy", concurrency=0)


@pytest.mark.usefixtures("_environment")
@pytest.mark.asyncio
async def test_export_template_keeps_binary_metadata_and_bounds_batches(
    mocker, tmp_path,
):
    export = template("export_documents.py")["export"]
    docs = {
        "/a.bin": Document.binary(
            "/a.bin", b"\x00\xff", metadata=Metadata(collections=["test"]),
        ),
        "/b.json": Document.json("/b.json", {"name": "b"}),
    }

    async def read(_service, uris, *, category):
        assert category == ["content", "metadata"]
        assert len(uris) <= 1
        return {uri: docs[uri] for uri in uris}

    mocker.patch.object(AsyncDocumentsService, "read", autospec=True, side_effect=read)
    target = tmp_path / "export"
    await export("test", "content", docs, str(target), batch_size=1)
    assert (target / "a.bin").read_bytes() == b"\x00\xff"
    assert "test" in (target / "a.metadata.json").read_text()
    assert "b" in (target / "b.json").read_text()


@pytest.mark.usefixtures("_environment")
@pytest.mark.asyncio
async def test_export_template_rejects_invalid_batch_size(tmp_path):
    export = template("export_documents.py")["export"]
    with pytest.raises(ValueError, match="positive"):
        await export("test", "content", [], str(tmp_path), batch_size=0)


@pytest.mark.usefixtures("_environment")
@pytest.mark.asyncio
@pytest.mark.parametrize("uri", ["/../escaped.json", "relative.json", "//tmp/escaped"])
async def test_export_template_rejects_unsafe_paths_before_request(
    tmp_path, uri,
):
    export = template("export_documents.py")["export"]
    with pytest.raises(ValueError, match="Unsafe export URI"):
        await export("test", "content", [uri], str(tmp_path / "export"))


@pytest.mark.usefixtures("_environment")
@pytest.mark.asyncio
async def test_export_template_rejects_metadata_symlink_escape(tmp_path):
    export = template("export_documents.py")["export"]
    target = tmp_path / "export"
    target.mkdir()
    victim = tmp_path / "victim"
    victim.write_text("keep")
    (target / "a.metadata.json").symlink_to(victim)
    with pytest.raises(ValueError, match="Unsafe export URI"):
        await export("test", "content", ["/a.json"], str(target))
    assert victim.read_text() == "keep"


@pytest.mark.usefixtures("_environment")
@pytest.mark.asyncio
async def test_custom_client_templates_send_correct_requests_sync_and_async(
):
    module = template("custom_api.py")
    with respx.mock as router:
        route = router.get(
            "http://localhost:8100/app/tasks", params={"status": "open"},
        ).mock(
            return_value=httpx.Response(200, json={"tasks": []}),
        )
        config = MLClientManager("test").get_config("content")
        with module["MyAppMLClient"](config=config) as ml:
            response = ml.rest.my_awesome_endpoint(timeout=7)
            assert response.json() == {"tasks": []}
        async with module["AsyncMyAppMLClient"](config=config) as ml:
            response = await ml.rest.my_awesome_endpoint(timeout=8)
            assert response.json() == {"tasks": []}
        assert route.call_count == 2
        assert route.calls[0].request.headers["accept"] == "application/json"
        assert route.calls[0].request.extensions["timeout"]["read"] == 7
        assert route.calls[1].request.extensions["timeout"]["read"] == 8


def test_bundled_resource_inventory_is_available_without_mcp_import():
    skill = files("mlclient").joinpath("resources", "skills", "mlclient")
    assert skill.joinpath("SKILL.md").is_file()
    assert (
        skill.joinpath("assets", "search_page.xqy")
        .read_text()
        .startswith("xquery version")
    )


@pytest.mark.usefixtures("_environment")
@pytest.mark.asyncio
async def test_uri_template_keeps_cursor_lookahead_and_fixed_forest_scope(mocker):
    pages = template("uri_pages.py")["uri_pages"]
    evaluate = mocker.patch.object(
        AsyncEvalService, "expression",
        side_effect=[["/a", "/b", "/c"], ["/c", "/d", "/e"], "/e"],
    )
    query = cts.collection_query("orders")
    async with MLClientManager("test").get_async_client("content") as ml:
        result = [batch async for batch in pages(
            ml, query, batch_size=2, forest_ids=[101, 102], database="Orders",
        )]
    assert result == [["/a", "/b"], ["/c", "/d"], ["/e"]]
    assert evaluate.await_count == 3
    for call, cursor in zip(evaluate.call_args_list, ["", "/c", "/e"]):
        code, variables = call.args[0].compile()
        cursor_name = re.search(r"cts:uris\(\$(\w+)", code).group(1)
        assert variables[cursor_name] == cursor
        first, last = re.search(r"\[\$(\w+) to \$(\w+)\]", code).groups()
        assert int(variables[first]) == 1
        assert int(variables[last]) == 3
        assert "101" in variables.values()
        assert "102" in variables.values()
        assert call.kwargs == {"database": "Orders"}


@pytest.mark.usefixtures("_environment")
@pytest.mark.asyncio
async def test_uri_template_finishes_empty_scope_and_bounds_final_page(mocker):
    pages = template("uri_pages.py")["uri_pages"]
    evaluate = mocker.patch.object(AsyncEvalService, "expression", return_value=[])
    async with MLClientManager("test").get_async_client("content") as ml:
        assert [page async for page in pages(ml, cts.true_query())] == []
        evaluate.return_value = ["/a", "/b"]
        assert [page async for page in pages(
            ml, cts.true_query(), batch_size=2,
        )] == [["/a", "/b"]]
    assert evaluate.await_count == 2


@pytest.mark.parametrize("options", [{"batch_size": 0}, {"batch_size": True},
                                     {"batch_size": "10"}, {"forest_ids": []}])
@pytest.mark.asyncio
async def test_uri_template_rejects_invalid_bounds_before_io(options):
    pages = template("uri_pages.py")["uri_pages"]
    with pytest.raises(ValueError, match="batch_size"):
        await pages(None, cts.true_query(), **options).__anext__()


@pytest.mark.asyncio
async def test_uri_template_requires_a_builder():
    pages = template("uri_pages.py")["uri_pages"]
    with pytest.raises(TypeError, match="builder"):
        await pages(None, "cts:true-query()").__anext__()


@pytest.mark.usefixtures("_environment")
@pytest.mark.parametrize("value", [123, ["/a", "/b", ""]])
@pytest.mark.asyncio
async def test_uri_template_rejects_bad_values_and_stalled_cursor(mocker, value):
    pages = template("uri_pages.py")["uri_pages"]
    mocker.patch.object(AsyncEvalService, "expression", return_value=value)
    async with MLClientManager("test").get_async_client("content") as ml:
        with pytest.raises((TypeError, ValueError)):
            await pages(ml, cts.true_query(), batch_size=2).__anext__()


@pytest.mark.usefixtures("_environment")
@pytest.mark.asyncio
async def test_uri_template_retains_successor_when_boundary_uri_disappears(mocker):
    pages = template("uri_pages.py")["uri_pages"]
    evaluate = mocker.patch.object(
        AsyncEvalService, "expression",
        side_effect=[["/a", "/b", "/c"], ["/d", "/e"]],
    )
    async with MLClientManager("test").get_async_client("content") as ml:
        result = [batch async for batch in pages(ml, cts.true_query(), batch_size=2)]
    assert result == [["/a", "/b"], ["/d", "/e"]]
    assert evaluate.await_count == 2
