from __future__ import annotations

import subprocess
import sys
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
        "protocol",
        configs["dev"],
        default=False,
        reveal=False,
        identical=True,
    )
    assert cell == "<fg=green>https</>"


def test_marks_differing_values_yellow() -> None:
    configs = {"dev": {"host": "dev.example.com"}, "test": {"host": "test.example.com"}}

    assert _is_identical("host", ["dev", "test"], configs) is False
    cell = _compare_cell(
        "host",
        configs["dev"],
        default=False,
        reveal=False,
        identical=False,
    )
    assert cell == "<fg=yellow>dev.example.com</>"


def test_marks_a_differing_default_blue_and_tags_it() -> None:
    cell = _compare_cell(
        "port",
        {"port": 8002},
        default=True,
        reveal=False,
        identical=False,
    )
    assert cell == "<fg=blue>8002</> <options=italic>(default)</>"


def test_matching_default_stays_green_and_is_tagged() -> None:
    cell = _compare_cell(
        "username",
        {"username": "admin"},
        default=True,
        reveal=False,
        identical=True,
    )
    assert cell == "<fg=green>admin</> <options=italic>(default)</>"


def test_missing_setting_is_not_identical_and_renders_dash() -> None:
    configs = {"dev": {"host": "dev.example.com"}, "test": {}}

    assert _is_identical("host", ["dev", "test"], configs) is False
    assert (
        _compare_cell(
            "host",
            configs["test"],
            default=True,
            reveal=False,
            identical=False,
        )
        == "<fg=default;options=dark>-</>"
    )


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
    _write_env("dev", {"host": "shared.example.com"})
    _write_env("test", {"host": "shared.example.com"})

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


# --- secrets and literal output ---


@pytest.mark.parametrize("flag", ["", "-s", "--secrets"])
@pytest.mark.parametrize("server", [False, True])
def test_masks_supported_secrets(flag, server):
    settings = {
        "password": "private-password",
        "auth": {"method": "oauth", "token": "private-token"},
        "ssl": {"key_password": "private-key-password"},
    }
    config = {"app-servers": [{"id": "content", **settings}]} if server else settings
    _write_env("dev", config)

    tester = _get_tester()
    tester.execute(f"dev {flag}")

    assert tester.status_code == 0
    output = tester.io.fetch_output()

    for secret in ("private-password", "private-token", "private-key-password"):
        assert (secret in output) is bool(flag)


@pytest.mark.parametrize("flag", ["", "--secrets"])
def test_masks_cloud_api_key(flag):
    _write_env(
        "dev", {"cloud": {"api-key": "private-api-key", "base-path": "/endpoint"}},
    )

    tester = _get_tester()
    tester.execute(f"dev {flag}")

    assert tester.status_code == 0
    output = tester.io.fetch_output()

    assert ("private-api-key" in output) is bool(flag)


@pytest.mark.parametrize("decorated", [False, True])
def test_preserves_literal_markup(decorated):
    _write_env(
        "<info>dev",
        {
            "host": "<info>literal.example.com</info>",
            "app-servers": [
                {"id": "<info>content</info>", "username": "<error>alice</error>"},
            ],
        },
    )

    tester = _get_tester()
    tester.execute("'<info>dev'", decorated=decorated)

    assert tester.status_code == 0
    output = tester.io.fetch_output()

    assert "<info>dev" in output
    assert "<info>content</info>" in output
    assert "<info>literal.example.com</info>" in output
    assert "<error>alice</error>" in output


@pytest.mark.parametrize(
    ("other_token", "color"),
    [("first-token", "32"), ("second-token", "33")],
)
def test_comparison_colors_secrets_using_real_values(other_token, color):
    _write_env("dev", {"auth": {"method": "oauth", "token": "first-token"}})
    _write_env("other", {"auth": {"method": "oauth", "token": other_token}})

    tester = _get_tester()
    tester.execute("dev other", decorated=True)

    assert tester.status_code == 0
    output = tester.io.fetch_output()

    assert "first-token" not in output
    assert "second-token" not in output
    assert output.count(f"\x1b[{color}mmethod=oauth, token=****, service=HTTP") == 2


# --- defaults and inheritance ---


@pytest.mark.parametrize("content", ["", "# Empty\n", "null\n", "app-servers: null\n"])
def test_empty_environment_resolves_defaults(content):
    path = _write_env("dev", {})
    path.write_text(content)

    tester = _get_tester()
    tester.execute("dev --defaults")

    assert tester.status_code == 0
    output = tester.io.fetch_output()

    assert "localhost" in output
    assert "app-services" in output
    assert "8002" in output


def test_comparison_reads_each_environment_once(mocker):
    path = _write_env("dev", {"host": "dev.example.com"})
    read = mocker.spy(Path, "open")

    tester = _get_tester()
    tester.execute("dev")

    assert tester.status_code == 0

    reads = [call for call in read.call_args_list if call.args[0] == path]
    assert len(reads) == 1


def test_comparison_matches_inherited_values_to_explicit_values():
    _write_env("dev", {"username": "alice", "app-servers": [{"id": "content"}]})
    _write_env(
        "other",
        {
            "username": "alice",
            "app-servers": [{"id": "content", "port": 8000, "username": "alice"}],
        },
    )

    tester = _get_tester()
    tester.execute("dev other", decorated=True)

    assert tester.status_code == 0
    output = tester.io.fetch_output()
    content = output[output.index("content") :]

    assert content.count("\x1b[32malice\x1b[39m") == 2
    assert content.count("\x1b[32m8000\x1b[39m") == 2
    assert "(default)" in content


def test_compare_distinguishes_no_auth_from_inherited_auth():
    _write_env("dev", {"app-servers": [{"id": "content", "auth": "app"}]})
    _write_env("other", {"app-servers": [{"id": "content"}]})

    tester = _get_tester()
    tester.execute("dev other", decorated=True)

    assert tester.status_code == 0
    output = tester.io.fetch_output()

    assert "\x1b[33mapp\x1b[39m" in output
    assert "\x1b[34mdigest\x1b[39m" in output


def test_comparison_keeps_differing_inherited_settings():
    _write_env("dev", {"username": "alice", "app-servers": [{"id": "content"}]})
    _write_env("other", {"username": "bob", "app-servers": [{"id": "content"}]})

    tester = _get_tester()
    tester.execute("dev other", decorated=True)

    assert tester.status_code == 0
    output = tester.io.fetch_output()
    content = output[output.index("content") :]

    assert "\x1b[34malice\x1b[39m" in content
    assert "\x1b[34mbob\x1b[39m" in content


def test_comparison_keeps_server_present_only_as_an_id():
    _write_env("dev", {"app-servers": [{"id": "content"}]})
    _write_env("other", {})

    tester = _get_tester()
    tester.execute("dev other")

    assert tester.status_code == 0
    output = tester.io.fetch_output()

    assert "content" in output
    assert "8000 (default)" in output


# --- safe error reporting ---


@pytest.mark.parametrize("verbosity", ["", "-vvv"])
def test_invalid_config_errors_do_not_disclose_input(verbosity):
    path = _write_env(
        "dev",
        {
            "auth": {"method": "oauth", "token": "private-token", "hostname": []},
        },
    )
    arguments = ["env", "compare", "dev", "--no-ansi"]
    if verbosity:
        arguments.append(verbosity)

    result = subprocess.run(
        [sys.executable, "-c", "from mlclient.cli import main; main()", *arguments],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )

    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert path.name in output
    assert "hostname" in output
    assert "private-token" not in output
    assert "input_value" not in output


def test_invalid_yaml_errors_do_not_disclose_input_at_debug_verbosity():
    path = _write_env("dev", {})
    path.write_text("password: [private-password")

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "from mlclient.cli import main; main()",
            "env",
            "compare",
            "dev",
            "--no-ansi",
            "-vvv",
        ],
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )

    output = result.stdout + result.stderr
    assert result.returncode != 0
    assert path.name in output
    assert "Invalid YAML" in output
    assert "private-password" not in output
