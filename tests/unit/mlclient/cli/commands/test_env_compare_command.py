from __future__ import annotations

from pathlib import Path

import pytest
import yaml
from cleo.testers.command_tester import CommandTester

from mlclient.cli import MLCLIentApplication
from mlclient.cli.commands.env_compare import (
    _compare_cell,
    _declared_servers,
    _is_identical,
    _union_keys,
)
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
    return CommandTester(app.find("env compare"))


def _write_env(name: str, config: dict, *, directory: Path | None = None) -> Path:
    directory = directory or Path.cwd() / ".mlclient"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"mlclient-{name}.yaml"
    path.write_text(yaml.safe_dump(config))
    return path


# --- comparison logic ---


def test_marks_identical_explicit_values_green() -> None:
    configs = {"dev": {"protocol": "https"}, "test": {"protocol": "https"}}

    assert _is_identical("protocol", ["dev", "test"], configs) is True
    cell = _compare_cell(
        "protocol", configs["dev"], default=False, reveal=False, identical=True,
    )
    assert cell == "<fg=green>https</>"


def test_marks_differing_values_yellow() -> None:
    configs = {"dev": {"host": "dev.example.com"}, "test": {"host": "test.example.com"}}

    assert _is_identical("host", ["dev", "test"], configs) is False
    cell = _compare_cell(
        "host", configs["dev"], default=False, reveal=False, identical=False,
    )
    assert cell == "<fg=yellow>dev.example.com</>"


def test_marks_a_differing_default_blue_and_tags_it() -> None:
    cell = _compare_cell(
        "port", {"port": 8002}, default=True, reveal=False, identical=False,
    )
    assert cell == "<fg=blue>8002</> <options=italic>(default)</>"


def test_matching_default_stays_green_and_is_tagged() -> None:
    cell = _compare_cell(
        "username", {"username": "admin"}, default=True, reveal=False, identical=True,
    )
    assert cell == "<fg=green>admin</> <options=italic>(default)</>"


def test_missing_setting_is_not_identical_and_renders_dash() -> None:
    configs = {"dev": {"host": "dev.example.com"}, "test": {}}

    assert _is_identical("host", ["dev", "test"], configs) is False
    assert _compare_cell(
        "host", configs["test"], default=True, reveal=False, identical=False,
    ) == "<fg=default;options=dark>-</>"


def test_union_keeps_first_seen_order() -> None:
    configs = {"dev": {"host": "h", "auth": "digest"}, "test": {"port": 1, "host": "h"}}

    assert _union_keys(["dev", "test"], configs) == ["host", "auth", "port"]


def test_declared_servers_maps_ids_to_user_fields() -> None:
    raw = {"app-servers": [{"id": "manage", "port": 8002}, {"id": "content"}]}

    declared = _declared_servers(raw)

    assert declared == {"manage": {"port": 8002}, "content": {}}


# --- rendering ---


def test_compares_named_environments() -> None:
    _write_env("dev", {"host": "dev.example.com", "protocol": "https"})
    _write_env("test", {"host": "test.example.com", "protocol": "https"})

    tester = _get_tester()
    tester.execute("dev test")

    output = tester.io.fetch_output()
    assert tester.status_code == 0
    assert "dev.example.com" in output
    assert "test.example.com" in output


def test_compares_all_environments_by_default() -> None:
    _write_env("dev", {"host": "dev.example.com"})
    _write_env("test", {"host": "test.example.com"})

    tester = _get_tester()
    tester.execute("")

    output = tester.io.fetch_output()
    assert "dev.example.com" in output
    assert "test.example.com" in output


def test_excludes_named_environments_from_the_default_set() -> None:
    _write_env("local", {"host": "local.example.com"})
    _write_env("dev", {"host": "dev.example.com"})
    _write_env("test", {"host": "test.example.com"})

    tester = _get_tester()
    tester.execute("--exclude local")

    output = tester.io.fetch_output()
    assert "local.example.com" not in output
    assert "dev.example.com" in output
    assert "test.example.com" in output


def test_masks_secrets_by_default() -> None:
    _write_env("dev", {"password": "hunter2"})
    _write_env("test", {"password": "swordfish"})

    tester = _get_tester()
    tester.execute("dev test")

    output = tester.io.fetch_output()
    assert "hunter2" not in output
    assert "swordfish" not in output
    assert "****" in output


def test_reveals_secrets_with_flag() -> None:
    _write_env("dev", {"password": "hunter2"})

    tester = _get_tester()
    tester.execute("dev --secrets")

    assert "hunter2" in tester.io.fetch_output()


def test_renders_a_table_per_app_server() -> None:
    _write_env(
        "dev",
        {
            "host": "dev.example.com",
            "app-servers": [
                {"id": "manage", "port": 8002},
                {"id": "content", "port": 8010},
            ],
        },
    )
    _write_env(
        "test",
        {"host": "test.example.com", "app-servers": [{"id": "manage", "port": 8102}]},
    )

    tester = _get_tester()
    tester.execute("dev test")

    output = tester.io.fetch_output()
    assert "manage" in output
    assert "content" in output
    assert "8002" in output
    assert "8102" in output
    assert "8010" in output


def test_fills_in_default_root_settings_an_environment_leaves_unset() -> None:
    _write_env("dev", {"host": "dev.example.com", "username": "super"})
    _write_env("test", {"host": "test.example.com"})

    tester = _get_tester()
    tester.execute("dev test")

    output = tester.io.fetch_output()
    assert "super" in output
    assert "admin" in output


def test_omits_settings_left_to_their_default_in_every_environment() -> None:
    _write_env("dev", {"host": "dev.example.com"})
    _write_env("test", {"host": "test.example.com"})

    tester = _get_tester()
    tester.execute("dev test")

    output = tester.io.fetch_output()
    assert "host" in output
    for shared_default in ("username", "manage", "admin", "app-services", "health"):
        assert shared_default not in output


def test_defaults_flag_keeps_settings_default_across_every_environment() -> None:
    _write_env("dev", {"host": "dev.example.com"})
    _write_env("test", {"host": "test.example.com"})

    tester = _get_tester()
    tester.execute("dev test --defaults")

    output = tester.io.fetch_output()
    assert "username" in output
    for server_id in ("app-services", "manage", "admin", "health"):
        assert server_id in output


def test_platform_server_overridden_in_one_env_shows_default_for_others() -> None:
    _write_env("dev", {"app-servers": [{"id": "manage", "port": 9002}]})
    _write_env("test", {"host": "test.example.com"})

    tester = _get_tester()
    tester.execute("dev test")

    output = tester.io.fetch_output()
    assert "manage" in output
    assert "9002" in output
    assert "8002" in output


def test_server_present_in_one_environment_only_renders_dash_for_the_other() -> None:
    _write_env("dev", {"app-servers": [{"id": "search", "port": 9000}]})
    _write_env("test", {"host": "test.example.com"})

    tester = _get_tester()
    tester.execute("dev test")

    output = tester.io.fetch_output()
    assert "search" in output
    assert "9000" in output


# --- directory resolution and errors ---


def test_reads_global_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path / "home"
    _write_env("dev", {"host": "home.example.com"}, directory=home / ".mlclient")
    monkeypatch.setattr(Path, "home", lambda: home)

    tester = _get_tester()
    tester.execute("dev --global")

    output = tester.io.fetch_output()
    assert "home.example.com" in output
    assert "Reading" not in output


def test_flags_fall_through_to_global(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    home = tmp_path
    _write_env("dev", {"host": "home.example.com"}, directory=home / ".mlclient")
    monkeypatch.setattr(Path, "home", lambda: home)
    nested = tmp_path / "project"
    nested.mkdir()
    monkeypatch.chdir(nested)

    tester = _get_tester()
    tester.execute("dev")

    assert "Reading" in tester.io.fetch_output()


def test_errors_when_named_environment_missing() -> None:
    _write_env("dev", {"host": "dev.example.com"})

    tester = _get_tester()
    with pytest.raises(WrongParametersError) as error:
        tester.execute("dev nope")

    assert "No environment [nope]" in str(error.value)
    assert "Available: dev" in str(error.value)


def test_reports_no_environments_when_directory_empty() -> None:
    tester = _get_tester()
    tester.execute("")

    assert tester.status_code == 0
    assert "No environments found" in tester.io.fetch_output()
