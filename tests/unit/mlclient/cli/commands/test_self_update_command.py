"""Verify self-update through CLI effects and package-manager process boundaries."""

import importlib.util
import shutil
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest
from cleo.testers.command_tester import CommandTester

from mlclient.cli import MLCLIentApplication
from mlclient.exceptions import WrongParametersError


@pytest.fixture(autouse=True)
def directories(tmp_path, monkeypatch):
    project = tmp_path / "project"
    home = tmp_path / "home"
    prefix = tmp_path / "venv"
    for path in (project, home, prefix):
        path.mkdir()
    monkeypatch.chdir(project)
    monkeypatch.setattr(Path, "home", lambda: home)
    monkeypatch.setattr(sys, "prefix", str(prefix))
    monkeypatch.delenv("CODEX_HOME", raising=False)
    monkeypatch.setattr(importlib.util, "find_spec", lambda _: None)
    monkeypatch.setattr(shutil, "which", lambda name: "/tools/" + name)
    return project, home, prefix


def command(name="self update"):
    return CommandTester(MLCLIentApplication().find(name))


@pytest.mark.parametrize(
    ("manager", "expected"),
    [
        ("pipx", ["/tools/pipx", "upgrade", "mlclient"]),
        ("uv", ["/tools/uv", "tool", "upgrade", "mlclient"]),
        ("pip", [sys.executable, "-m", "pip", "install", "--upgrade", "mlclient"]),
        ("uv-pip", ["/tools/uv", "pip", "install", "--upgrade", "mlclient"]),
    ],
)
def test_upgrade_uses_owning_manager_and_pypi(
    directories, monkeypatch, manager, expected,
):
    _, _, prefix = directories
    marker = {"pipx": "pipx_metadata.json", "uv": "uv-receipt.toml"}.get(manager)
    if marker:
        (prefix / marker).write_text("")
    if manager == "pip":
        monkeypatch.setattr(importlib.util, "find_spec", lambda name: name == "pip")
    calls = []

    def run(args, **kwargs):
        calls.append((args, kwargs))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", run)
    tester = command()
    assert tester.execute() == 0
    assert len(calls) == 1
    assert calls[0][0][: len(expected)] == expected
    assert any("https://pypi.org/simple" in arg for arg in calls[0][0])
    if manager == "uv-pip":
        assert calls[0][0][5:7] == ["--python", sys.executable]
    assert "updated" in tester.io.fetch_output()




def test_refreshes_recorded_other_project_and_legacy_global_install(
    directories,
    monkeypatch,
):
    project, home, _ = directories
    other = project.parent / "other"
    other.mkdir()
    monkeypatch.chdir(other)
    command("install skill").execute("codex")
    skill = other / ".agents/skills/mlclient/SKILL.md"
    skill.write_text("old skill")
    monkeypatch.chdir(project)
    global_skill = home / ".claude/skills/mlclient/SKILL.md"
    global_skill.parent.mkdir(parents=True)
    global_skill.write_text("old global skill")
    calls = []

    def run(args, **kwargs):
        calls.append((args, kwargs))
        if "install" in args and args[1] == "-c":
            assert "from mlclient.cli import main" in args[2]
            with monkeypatch.context() as context:
                context.chdir(kwargs["cwd"])
                tester = command("install " + args[4])
                tester.execute(" ".join(args[5:]))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(subprocess, "run", run)
    assert command().execute() == 0
    assert len(calls) == 3
    assert calls[1][1]["cwd"] == str(other)
    assert "name: mlclient" in skill.read_text()
    assert "--global" in calls[2][0]
    assert "name: mlclient" in global_skill.read_text()
    assert not (project / ".agents").exists()


def test_dry_run_reports_plan_without_processes_or_writes(directories, monkeypatch):
    project, home, _ = directories
    target = project / ".cursor/skills/mlclient"
    target.mkdir(parents=True)
    (target / "SKILL.md").write_text("old")
    calls = []
    monkeypatch.setattr(subprocess, "run", lambda *args, **_: calls.append(args))
    tester = command()
    assert tester.execute("--dry-run") == 0
    assert "Refresh skill for cursor" in tester.io.fetch_output()
    assert (target / "SKILL.md").read_text() == "old"
    assert not any(home.iterdir())
    assert not calls


@pytest.mark.parametrize(
    ("failed_call", "message"), [(1, "upgrade failed"), (2, "refresh failed")],
)
def test_failure_is_reported_without_running_later_steps(
    directories,
    monkeypatch,
    failed_call,
    message,
):
    project, _, _ = directories
    for agent in ("codex", "cursor"):
        command("install skill").execute(agent)
    calls = []

    def run(args, **_):
        calls.append(args)
        return SimpleNamespace(returncode=7 if len(calls) == failed_call else 0)

    monkeypatch.setattr(subprocess, "run", run)
    tester = command()
    assert tester.execute() == 7
    assert len(calls) == failed_call
    assert message in tester.io.fetch_error()
    assert (project / ".agents/skills/mlclient/SKILL.md").exists()


def test_skips_removed_installations(directories, monkeypatch):
    project, _, _ = directories
    command("install skill").execute("codex")
    shutil.rmtree(project / ".agents")
    calls = []
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda args, **_: calls.append(args) or SimpleNamespace(returncode=0),
    )
    command().execute()
    assert len(calls) == 1


def test_ancestor_project_is_refreshed_only_once(directories, monkeypatch):
    project, _, _ = directories
    command("install skill").execute("codex")
    nested = project / "src"
    nested.mkdir()
    monkeypatch.chdir(nested)
    calls = []
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda args, **kwargs: (
            calls.append((args, kwargs)) or SimpleNamespace(returncode=0)
        ),
    )
    command().execute()
    assert len(calls) == 2
    assert calls[1][1]["cwd"] == str(project)


@pytest.mark.parametrize("manager", ["pipx", "uv", "uv-pip"])
def test_missing_manager_fails_before_any_upgrade(directories, monkeypatch, manager):
    _, _, prefix = directories
    marker = {"pipx": "pipx_metadata.json", "uv": "uv-receipt.toml"}.get(manager)
    if marker:
        (prefix / marker).write_text("")
    monkeypatch.setattr(shutil, "which", lambda _: None)
    with pytest.raises(WrongParametersError, match="requires"):
        command().execute()


@pytest.mark.parametrize("content", ["invalid", "{}", '[{"kind":"other"}]'])
def test_invalid_registry_is_not_overwritten(directories, content):
    _, home, _ = directories
    directory = home / ".mlclient"
    directory.mkdir()
    path = directory / "ai-installations.json"
    path.write_text(content)
    with pytest.raises(WrongParametersError, match="registry"):
        command().execute("--dry-run")
    with pytest.raises(WrongParametersError, match="registry"):
        command("install skill").execute("claude")
    assert path.read_text() == content
