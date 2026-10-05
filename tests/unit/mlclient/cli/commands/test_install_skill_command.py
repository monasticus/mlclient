"""Exercise skill installation through CLI commands and filesystem results."""

import json
import stat
from pathlib import Path

import pytest
from cleo.testers.command_tester import CommandTester

from mlclient.cli import MLCLIentApplication
from mlclient.exceptions import WrongParametersError

SKILLS = {
    "codex": ".agents/skills/mlclient",
    "claude": ".claude/skills/mlclient",
    "cursor": ".cursor/skills/mlclient",
    "copilot": ".github/skills/mlclient",
}


@pytest.fixture(autouse=True)
def project(tmp_path, monkeypatch):
    work = tmp_path / "project"
    home = tmp_path / "home"
    work.mkdir()
    home.mkdir()
    monkeypatch.chdir(work)
    monkeypatch.setattr(Path, "home", lambda: home)
    return work, home


def command():
    return CommandTester(MLCLIentApplication().find("install skill"))


@pytest.mark.parametrize("agent", SKILLS)
def test_install_has_complete_references_templates_and_tracking(project, agent):
    work, home = project
    tester = command()
    tester.execute(agent)
    destination = work / SKILLS[agent]
    assert "name: mlclient" in (destination / "SKILL.md").read_text()
    template = destination / "assets/concurrent_eval.py"
    assert "async def evaluate" in template.read_text()
    assert "**Request Headers**" in (
        destination / "references/endpoints/v12.md"
    ).read_text()
    output = tester.io.fetch_output()
    for path in destination.rglob("*"):
        if path.is_file():
            assert str(path) in output
    assert "Restart" in output
    registry = home / ".mlclient/ai-installations.json"
    assert json.loads(registry.read_text()) == [
        {"agent": agent, "root": str(work), "global": False},
    ]
    assert str(registry) in output


@pytest.mark.parametrize("agent", SKILLS)
@pytest.mark.parametrize("scope", ["--global", "-g"])
def test_global_skill_uses_user_directory(project, agent, scope):
    work, home = project
    command().execute(f"{agent} {scope}")
    relative = ".copilot/skills/mlclient" if agent == "copilot" else SKILLS[agent]
    assert (home / relative / "SKILL.md").exists()
    assert not any(work.iterdir())


def test_missing_agent_prompts():
    tester = command()
    tester.execute(inputs="1\n", interactive=True)
    output = tester.io.fetch_output() + tester.io.fetch_error()
    assert "Install for which agent" in output


@pytest.mark.parametrize("selector", ["", "unknown"])
def test_noninteractive_selector_validation(selector):
    with pytest.raises(WrongParametersError, match="Choose an agent"):
        command().execute(selector, interactive=False)


def test_dry_run_creates_nothing(project):
    work, home = project
    tester = command()
    tester.execute("codex --dry-run")
    assert "Would write" in tester.io.fetch_output()
    assert not any(work.iterdir())
    assert not any(home.iterdir())


def test_identical_reinstall_does_not_rewrite_files(project):
    work, home = project
    command().execute("codex")
    skill = work / SKILLS["codex"] / "SKILL.md"
    registry = home / ".mlclient/ai-installations.json"
    modified = skill.stat().st_mtime_ns, registry.stat().st_mtime_ns
    tester = command()
    tester.execute("codex")
    assert (skill.stat().st_mtime_ns, registry.stat().st_mtime_ns) == modified
    assert "Unchanged" in tester.io.fetch_output()


def test_conflict_preflight_preserves_every_file(project):
    work, _ = project
    target = work / SKILLS["codex"]
    conflict = target / "references/search.md"
    conflict.parent.mkdir(parents=True)
    conflict.write_text("custom content")
    with pytest.raises(WrongParametersError, match="--force"):
        command().execute("codex")
    assert conflict.read_text() == "custom content"
    assert not (target / "SKILL.md").exists()
    command().execute("codex --force")
    assert "Index" in conflict.read_text()


@pytest.mark.parametrize("force", ["--force", "-f"])
def test_force_preserves_unrelated_files_and_permissions(project, force):
    work, _ = project
    command().execute("cursor")
    target = work / SKILLS["cursor"]
    custom = target / "custom.txt"
    custom.write_text("keep")
    skill = target / "SKILL.md"
    skill.write_text("old")
    skill.chmod(0o640)
    command().execute(f"cursor {force}")
    assert custom.read_text() == "keep"
    assert stat.S_IMODE(skill.stat().st_mode) == 0o640


def test_symlink_destination_is_rejected(project):
    work, home = project
    target = work / ".agents"
    target.symlink_to(home, target_is_directory=True)
    with pytest.raises(WrongParametersError, match="symlink"):
        command().execute("codex --force")
    assert not any(home.iterdir())


def test_failed_atomic_replace_keeps_old_file(project, monkeypatch):
    work, _ = project
    target = work / SKILLS["codex"]
    target.mkdir(parents=True)
    skill = target / "SKILL.md"
    skill.write_text("old")

    def fail_replace(_self, _target):
        message = "cannot replace"
        raise OSError(message)

    monkeypatch.setattr(Path, "replace", fail_replace)
    with pytest.raises(OSError, match="cannot replace"):
        command().execute("codex --force")
    assert skill.read_text() == "old"
    assert list(target.iterdir()) == [skill]
