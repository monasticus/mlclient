from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from cleo.testers.command_tester import CommandTester

from mlclient.cli import MLCLIentApplication
from mlclient.exceptions import WrongParametersError


@pytest.fixture(autouse=True)
def _work_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _get_tester() -> CommandTester:
    app = MLCLIentApplication()
    return CommandTester(app.find("env show"))


def _write_env(name: str, config: dict) -> None:
    directory = Path.cwd() / ".mlclient"
    directory.mkdir(exist_ok=True)
    (directory / f"mlclient-{name}.yaml").write_text(yaml.safe_dump(config))


def test_lists_environments_when_no_name() -> None:
    _write_env("local", {"host": "localhost"})
    _write_env("dev", {"host": "dev.example.com"})

    tester = _get_tester()
    tester.execute("")

    output = tester.io.fetch_output()
    assert tester.status_code == 0
    assert "local" in output
    assert "dev" in output


def test_reports_no_environments_when_directory_empty() -> None:
    tester = _get_tester()
    tester.execute("")

    assert tester.status_code == 0
    assert "No environments" in tester.io.fetch_output()


def test_omits_directory_note_when_in_cwd() -> None:
    _write_env("dev", {"host": "dev.example.com"})

    tester = _get_tester()
    tester.execute("dev")

    assert "Reading" not in tester.io.fetch_output()


def test_locates_mlclient_directory_in_ancestor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _write_env("dev", {"host": "dev.example.com"})
    ancestor_dir = Path.cwd() / ".mlclient"
    nested = Path.cwd() / "sub" / "deeper"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    tester = _get_tester()
    tester.execute("dev")

    output = tester.io.fetch_output()
    assert tester.status_code == 0
    assert "dev.example.com" in output
    assert str(ancestor_dir) in output


def test_reads_global_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    (home / ".mlclient").mkdir(parents=True)
    (home / ".mlclient" / "mlclient-dev.yaml").write_text(
        yaml.safe_dump({"host": "home.example.com"}),
    )
    monkeypatch.setattr(Path, "home", lambda: home)

    tester = _get_tester()
    tester.execute("dev --global")

    output = tester.io.fetch_output()
    assert tester.status_code == 0
    assert "home.example.com" in output
    assert "Reading" not in output


def test_flags_implicit_fall_through_to_global(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path
    (home / ".mlclient").mkdir()
    (home / ".mlclient" / "mlclient-dev.yaml").write_text(
        yaml.safe_dump({"host": "home.example.com"}),
    )
    monkeypatch.setattr(Path, "home", lambda: home)
    nested = home / "sub" / "deeper"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    tester = _get_tester()
    tester.execute("dev")

    output = tester.io.fetch_output()
    assert tester.status_code == 0
    assert "home.example.com" in output
    assert str(home / ".mlclient") in output
    assert "(global)" in output


def test_renders_settings_and_masks_password() -> None:
    _write_env(
        "dev",
        {"host": "dev.example.com", "protocol": "https", "password": "s3cret"},
    )

    tester = _get_tester()
    tester.execute("dev")

    output = tester.io.fetch_output()
    assert tester.status_code == 0
    assert "dev.example.com" in output
    assert "https" in output
    assert "s3cret" not in output
    assert "****" in output


def test_renders_app_servers() -> None:
    _write_env(
        "dev",
        {
            "host": "dev.example.com",
            "app-servers": [
                {"id": "app-services", "rest": True},
                {"id": "manage", "port": 8002},
            ],
        },
    )

    tester = _get_tester()
    tester.execute("dev")

    output = tester.io.fetch_output()
    assert "app-services" in output
    assert "manage" in output
    assert "8002" in output


def test_full_view_omits_predefined_servers_absent_from_file() -> None:
    _write_env("dev", {"host": "dev.example.com"})

    tester = _get_tester()
    tester.execute("dev")

    output = tester.io.fetch_output()
    assert "manage" not in output
    assert "app-services" not in output


def test_masks_nested_secrets() -> None:
    _write_env(
        "cloud",
        {"host": "ml.example.com", "cloud": {"api-key": "topsecret"}},
    )

    tester = _get_tester()
    tester.execute("cloud")

    output = tester.io.fetch_output()
    assert "topsecret" not in output
    assert "****" in output


def test_show_secrets_reveals_password() -> None:
    _write_env("dev", {"host": "dev.example.com", "password": "s3cret"})

    tester = _get_tester()
    tester.execute("dev --secrets")

    output = tester.io.fetch_output()
    assert tester.status_code == 0
    assert "s3cret" in output
    assert "****" not in output


def test_raw_prints_file_verbatim_without_masking() -> None:
    _write_env("dev", {"host": "dev.example.com", "password": "s3cret"})

    tester = _get_tester()
    tester.execute("dev --raw")

    output = tester.io.fetch_output()
    assert tester.status_code == 0
    assert "password: s3cret" in output
    assert "****" not in output


def test_reports_unknown_environment() -> None:
    _write_env("dev", {"host": "dev.example.com"})
    tester = _get_tester()

    with pytest.raises(WrongParametersError) as error:
        tester.execute("prod")

    message = str(error.value)
    assert "prod" in message
    assert "dev" in message


def test_setting_prints_root_scalar_value() -> None:
    _write_env("dev", {"host": "dev.example.com", "protocol": "https"})

    tester = _get_tester()
    tester.execute("dev host")

    output = tester.io.fetch_output()
    assert tester.status_code == 0
    assert "dev.example.com" in output
    assert "Setting" not in output


def test_setting_masks_root_secret() -> None:
    _write_env("dev", {"host": "dev.example.com", "password": "s3cret"})

    tester = _get_tester()
    tester.execute("dev password")

    output = tester.io.fetch_output()
    assert "s3cret" not in output
    assert "****" in output


def test_setting_renders_app_server_table() -> None:
    _write_env(
        "dev",
        {
            "host": "dev.example.com",
            "app-servers": [
                {"id": "rest", "port": 3693, "rest": True},
                {"id": "manage", "port": 8002},
            ],
        },
    )

    tester = _get_tester()
    tester.execute("dev rest")

    output = tester.io.fetch_output()
    assert tester.status_code == 0
    assert "rest" in output
    assert "3693" in output
    assert "manage" not in output


def test_setting_renders_predefined_app_server_absent_from_file() -> None:
    _write_env("dev", {"host": "dev.example.com"})

    tester = _get_tester()
    tester.execute("dev manage")

    output = tester.io.fetch_output()
    assert tester.status_code == 0
    assert "manage" in output
    assert "8002" in output


def test_reports_unknown_setting() -> None:
    _write_env("dev", {"host": "dev.example.com"})
    tester = _get_tester()

    with pytest.raises(WrongParametersError) as error:
        tester.execute("dev nope")

    assert "nope" in str(error.value)
