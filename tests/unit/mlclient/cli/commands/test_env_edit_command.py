from __future__ import annotations

import shlex
import sys
from pathlib import Path
from unittest.mock import Mock

import pytest
import yaml
from cleo.testers.command_tester import CommandTester
from pytest_mock import MockerFixture

from mlclient.cli import MLCLIentApplication
from mlclient.exceptions import WrongParametersError


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
        "mlclient.cli.commands._env_editor.subprocess.call",
        return_value=0,
    )


def _get_tester() -> CommandTester:
    app = MLCLIentApplication()
    return CommandTester(app.find("env edit"))


def _write_env(name: str, config: dict) -> Path:
    directory = Path.cwd() / ".mlclient"
    directory.mkdir(exist_ok=True)
    path = directory / f"mlclient-{name}.yaml"
    path.write_text(yaml.safe_dump(config))
    return path


# --- launching the editor ---


def test_opens_resolved_file_with_default_editor(editor_call: Mock) -> None:
    path = _write_env("local", {"host": "localhost"})

    tester = _get_tester()
    tester.execute("local")

    assert tester.status_code == 0
    editor_call.assert_called_once_with(["vi", str(path)])


def test_prefers_visual_over_editor(
    editor_call: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EDITOR", "nano")
    monkeypatch.setenv("VISUAL", "code -w")
    path = _write_env("local", {"host": "localhost"})

    tester = _get_tester()
    tester.execute("local")

    editor_call.assert_called_once_with(["code", "-w", str(path)])


def test_falls_back_to_editor_when_no_visual(
    editor_call: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("EDITOR", "nano")
    path = _write_env("local", {"host": "localhost"})

    tester = _get_tester()
    tester.execute("local")

    editor_call.assert_called_once_with(["nano", str(path)])


def test_returns_editor_exit_status(editor_call: Mock) -> None:
    editor_call.return_value = 3
    _write_env("local", {"host": "localhost"})

    tester = _get_tester()
    tester.execute("local")

    assert tester.status_code == 3


# --- directory resolution (consistent with env show) ---


def test_locates_mlclient_directory_in_ancestor(
    editor_call: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    path = _write_env("dev", {"host": "dev.example.com"})
    nested = Path.cwd() / "sub" / "deeper"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    tester = _get_tester()
    tester.execute("dev")

    editor_call.assert_called_once_with(["vi", str(path)])


def test_edits_global_directory(
    editor_call: Mock,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    (home / ".mlclient").mkdir(parents=True)
    path = home / ".mlclient" / "mlclient-dev.yaml"
    path.write_text(yaml.safe_dump({"host": "home.example.com"}))
    monkeypatch.setattr(Path, "home", lambda: home)

    tester = _get_tester()
    tester.execute("dev --global")

    editor_call.assert_called_once_with(["vi", str(path)])


# --- missing environment ---


def test_errors_when_environment_missing(editor_call: Mock) -> None:
    _write_env("local", {"host": "localhost"})

    tester = _get_tester()
    with pytest.raises(WrongParametersError) as error:
        tester.execute("nope")

    assert "No environment [nope]" in str(error.value)
    assert "Available: local" in str(error.value)
    editor_call.assert_not_called()


def test_errors_when_no_mlclient_directory(editor_call: Mock) -> None:
    tester = _get_tester()
    with pytest.raises(WrongParametersError) as error:
        tester.execute("local")

    assert "No environment [local]" in str(error.value)
    editor_call.assert_not_called()


def test_editor_arguments_and_quoted_script_path(monkeypatch: pytest.MonkeyPatch):
    path = _write_env("local", {"host": "localhost"})
    script = Path.cwd() / "editor with spaces.py"
    script.write_text(
        "import sys\nfrom pathlib import Path\n"
        "assert sys.argv[1] == '--wait'\n"
        "Path(sys.argv[2]).write_text('host: edited.example.com\\n')\n"
        "sys.exit(3)\n",
    )
    monkeypatch.setenv("VISUAL", shlex.join([sys.executable, str(script), "--wait"]))
    tester = _get_tester()

    tester.execute("local")

    assert tester.status_code == 3
    assert path.read_text() == "host: edited.example.com\n"


@pytest.mark.parametrize("editor", ["   ", '"unterminated'])
def test_rejects_invalid_editor_command(editor, monkeypatch, editor_call):
    _write_env("local", {})
    monkeypatch.setenv("VISUAL", editor)

    with pytest.raises(WrongParametersError, match="VISUAL or EDITOR"):
        _get_tester().execute("local")

    editor_call.assert_not_called()
