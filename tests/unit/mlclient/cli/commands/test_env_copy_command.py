from __future__ import annotations

from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml
from cleo.testers.command_tester import CommandTester
from pytest_mock import MockerFixture

from mlclient.cli import MLCLIentApplication
from mlclient.exceptions import EnvironmentFileExistsError, WrongParametersError


@pytest.fixture(autouse=True)
def _work_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


@pytest.fixture
def editor_call(mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch) -> Mock:
    monkeypatch.delenv("VISUAL", raising=False)
    monkeypatch.delenv("EDITOR", raising=False)
    return mocker.patch(
        "mlclient.cli.commands.env_edit.subprocess.call",
        return_value=0,
    )


def _get_tester() -> CommandTester:
    app = MLCLIentApplication()
    return CommandTester(app.find("env copy"))


def _write_env(name: str, config: dict, *, directory: Path | None = None) -> Path:
    directory = directory or Path.cwd() / ".mlclient"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"mlclient-{name}.yaml"
    path.write_text(yaml.safe_dump(config))
    return path


def _read_env(name: str, *, directory: Path | None = None) -> str:
    directory = directory or Path.cwd() / ".mlclient"
    return (directory / f"mlclient-{name}.yaml").read_text()


# --- copying ---


def test_clones_source_to_target() -> None:
    _write_env("prod", {"host": "prod.example.com"})

    tester = _get_tester()
    tester.execute("prod prod-test")

    assert tester.status_code == 0
    assert _read_env("prod-test") == _read_env("prod")
    assert "prod-test" in tester.io.fetch_output()


def test_preserves_comments_verbatim() -> None:
    content = "# a comment\nhost: prod.example.com\n"
    directory = Path.cwd() / ".mlclient"
    directory.mkdir()
    (directory / "mlclient-prod.yaml").write_text(content)

    tester = _get_tester()
    tester.execute("prod prod-test")

    assert _read_env("prod-test") == content


def test_refuses_to_overwrite_target() -> None:
    _write_env("prod", {"host": "prod.example.com"})
    _write_env("prod-test", {"host": "stale.example.com"})

    tester = _get_tester()
    with pytest.raises(EnvironmentFileExistsError):
        tester.execute("prod prod-test")

    assert "stale.example.com" in _read_env("prod-test")


def test_force_overwrites_target() -> None:
    _write_env("prod", {"host": "prod.example.com"})
    _write_env("prod-test", {"host": "stale.example.com"})

    tester = _get_tester()
    tester.execute("prod prod-test --force")

    assert tester.status_code == 0
    assert "prod.example.com" in _read_env("prod-test")


def test_errors_when_source_missing() -> None:
    _write_env("prod", {"host": "prod.example.com"})

    tester = _get_tester()
    with pytest.raises(WrongParametersError) as error:
        tester.execute("nope prod-test")

    assert "No environment [nope]" in str(error.value)
    assert "Available: prod" in str(error.value)


def test_errors_when_no_mlclient_directory() -> None:
    tester = _get_tester()
    with pytest.raises(WrongParametersError) as error:
        tester.execute("prod prod-test")

    assert "No environment [prod]" in str(error.value)


# --- directory resolution (consistent with env show) ---


def test_copies_within_ancestor_directory(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ancestor = Path.cwd() / ".mlclient"
    _write_env("prod", {"host": "prod.example.com"}, directory=ancestor)
    nested = Path.cwd() / "sub" / "deeper"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    tester = _get_tester()
    tester.execute("prod prod-test")

    assert (ancestor / "mlclient-prod-test.yaml").is_file()


def test_copies_within_global_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    directory = home / ".mlclient"
    _write_env("prod", {"host": "prod.example.com"}, directory=directory)
    monkeypatch.setattr(Path, "home", lambda: home)

    tester = _get_tester()
    tester.execute("prod prod-test --global")

    assert (directory / "mlclient-prod-test.yaml").is_file()


# --- chaining into env edit ---


def test_edit_flag_opens_the_copy(editor_call: Mock) -> None:
    _write_env("prod", {"host": "prod.example.com"})

    tester = _get_tester()
    tester.execute("prod prod-test --edit")

    assert tester.status_code == 0
    target = Path.cwd() / ".mlclient" / "mlclient-prod-test.yaml"
    editor_call.assert_called_once_with(["vi", str(target)])


def test_edit_flag_carries_global(
    editor_call: Mock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    directory = home / ".mlclient"
    _write_env("prod", {"host": "prod.example.com"}, directory=directory)
    monkeypatch.setattr(Path, "home", lambda: home)

    tester = _get_tester()
    tester.execute("prod prod-test --global --edit")

    editor_call.assert_called_once_with(
        ["vi", str(directory / "mlclient-prod-test.yaml")],
    )


def test_without_edit_flag_does_not_open_editor(editor_call: Mock) -> None:
    _write_env("prod", {"host": "prod.example.com"})

    tester = _get_tester()
    tester.execute("prod prod-test")

    editor_call.assert_not_called()
