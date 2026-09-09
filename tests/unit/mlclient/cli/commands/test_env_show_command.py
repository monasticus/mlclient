from __future__ import annotations

import subprocess
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
def clipboard_process(mocker: MockerFixture, monkeypatch: pytest.MonkeyPatch) -> Mock:
    monkeypatch.setattr("mlclient.cli.commands.env_show.sys.platform", "linux")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    return mocker.patch("mlclient.cli.commands.env_show.subprocess.run")


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


def test_listing_ignores_copy(clipboard_process: Mock) -> None:
    _write_env("dev", {"host": "dev.example.com"})
    tester = _get_tester()

    tester.execute("--copy")

    assert tester.status_code == 0
    assert "dev" in tester.io.fetch_output()
    assert "only works for individual settings" in tester.io.fetch_error()
    clipboard_process.assert_not_called()


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


def test_full_view_ignores_copy(clipboard_process: Mock) -> None:
    _write_env("dev", {"host": "dev.example.com", "password": "s3cret"})
    tester = _get_tester()

    tester.execute("dev -c")

    output = tester.io.fetch_output()
    assert tester.status_code == 0
    assert "dev.example.com" in output
    assert "s3cret" not in output
    assert "****" in output
    assert "only works for individual settings" in tester.io.fetch_error()
    clipboard_process.assert_not_called()


@pytest.mark.parametrize("content", ["", "# Empty environment\n", "null\n"])
def test_renders_empty_environment(content: str) -> None:
    _write_env("dev", {})
    (Path.cwd() / ".mlclient" / "mlclient-dev.yaml").write_text(content)
    tester = _get_tester()

    tester.execute("dev")

    assert tester.status_code == 0
    assert "Setting" in tester.io.fetch_output()


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


@pytest.mark.parametrize("servers", [None, []])
def test_renders_environment_without_app_servers(servers: object) -> None:
    _write_env("dev", {"host": "dev.example.com", "app-servers": servers})
    tester = _get_tester()

    tester.execute("dev")

    assert tester.status_code == 0
    assert "dev.example.com" in tester.io.fetch_output()
    assert "App Servers" not in tester.io.fetch_output()


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


@pytest.mark.parametrize("secrets", [False, True])
def test_masks_secrets_in_lists(secrets: bool) -> None:
    items = [{"password": "list-secret"}, [{"api-key": "nested-secret"}]]
    _write_env(
        "dev",
        {"items": items},
    )
    tester = _get_tester()

    tester.execute("dev" + (" --secrets" if secrets else ""))

    output = tester.io.fetch_output()
    assert tester.status_code == 0
    assert ("list-secret" in output) is secrets
    assert ("nested-secret" in output) is secrets
    assert ("****" in output) is not secrets


@pytest.mark.parametrize("secrets", [False, True])
def test_masks_app_server_secrets_in_lists(secrets: bool) -> None:
    items = [{"password": "list-secret"}, [{"api-key": "nested-secret"}]]
    _write_env(
        "dev",
        {"app-servers": [{"id": "rest", "items": items}]},
    )
    tester = _get_tester()

    tester.execute("dev" + (" --secrets" if secrets else ""))

    output = tester.io.fetch_output()
    assert tester.status_code == 0
    assert ("list-secret" in output) is secrets
    assert ("nested-secret" in output) is secrets
    assert ("****" in output) is not secrets


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


def test_raw_prints_invalid_yaml_without_parsing() -> None:
    _write_env("dev", {})
    (Path.cwd() / ".mlclient" / "mlclient-dev.yaml").write_text("host: [")
    tester = _get_tester()

    tester.execute("dev --raw")

    assert tester.status_code == 0
    assert tester.io.fetch_output() == "host: [\n"


@pytest.mark.parametrize("arguments", ["dev --raw -c", "dev host --raw -c"])
def test_raw_ignores_copy(arguments: str, clipboard_process: Mock) -> None:
    _write_env("dev", {"host": "dev.example.com"})
    tester = _get_tester()

    tester.execute(arguments)

    assert tester.status_code == 0
    assert tester.io.fetch_output() == "host: dev.example.com\n"
    assert "--raw" in tester.io.fetch_error()
    clipboard_process.assert_not_called()


def test_reports_unknown_environment() -> None:
    _write_env("dev", {"host": "dev.example.com"})
    tester = _get_tester()

    with pytest.raises(WrongParametersError) as error:
        tester.execute("prod")

    message = str(error.value)
    assert "prod" in message
    assert "dev" in message


@pytest.mark.parametrize("config", [[], ["host"], "host", 1, False, ""])
def test_reports_non_mapping_environment(config: object) -> None:
    directory = Path.cwd() / ".mlclient"
    directory.mkdir()
    (directory / "mlclient-dev.yaml").write_text(yaml.safe_dump(config))
    tester = _get_tester()

    with pytest.raises(WrongParametersError, match="must be a mapping"):
        tester.execute("dev")


@pytest.mark.parametrize("servers", [{}, "rest", 1, False])
def test_reports_non_list_app_servers(servers: object) -> None:
    _write_env("dev", {"app-servers": servers})
    tester = _get_tester()

    with pytest.raises(WrongParametersError, match="app-servers must be a list"):
        tester.execute("dev")


@pytest.mark.parametrize(
    "server",
    [None, "rest", [], {}, {"id": 1}, {"id": ""}, {"id": " "}],
)
def test_reports_invalid_app_server(server: object) -> None:
    _write_env("dev", {"app-servers": [server]})
    tester = _get_tester()

    with pytest.raises(WrongParametersError, match="non-empty string id"):
        tester.execute("dev")


def test_reports_invalid_yaml_without_revealing_contents() -> None:
    _write_env("dev", {})
    path = Path.cwd() / ".mlclient" / "mlclient-dev.yaml"
    path.write_text("password: [secret-value")
    tester = _get_tester()

    with pytest.raises(WrongParametersError) as error:
        tester.execute("dev")

    message = str(error.value)
    assert "Invalid YAML" in message
    assert str(path) in message
    assert "secret-value" not in message


def test_setting_prints_root_scalar_value() -> None:
    _write_env("dev", {"host": "dev.example.com", "protocol": "https"})

    tester = _get_tester()
    tester.execute("dev host")

    output = tester.io.fetch_output()
    assert tester.status_code == 0
    assert "dev.example.com" in output
    assert "Setting" not in output


@pytest.mark.parametrize("flag", ["--copy", "-c"])
@pytest.mark.parametrize(
    ("value", "text"),
    [
        ("localhost", "localhost"),
        ("", ""),
        (0, "0"),
        (1.5, "1.5"),
        (True, "true"),
        (False, "false"),
        ("żółć\nline two", "żółć\nline two"),
    ],
)
def test_setting_copies_simple_value(
    flag: str,
    value: object,
    text: str,
    clipboard_process: Mock,
) -> None:
    _write_env("dev", {"setting": value})
    tester = _get_tester()

    tester.execute(f"dev setting {flag}")

    assert tester.status_code == 0
    assert tester.io.fetch_output() == f"{text}\nCopied to clipboard.\n"
    clipboard_process.assert_called_once()
    assert clipboard_process.call_args.kwargs["input"] == text.encode("utf-8")


def test_copy_confirmation_is_green_and_italic(clipboard_process: Mock) -> None:
    _write_env("dev", {"host": "localhost"})
    tester = _get_tester()

    tester.execute("dev host -c", decorated=True)

    assert tester.io.fetch_output() == (
        "localhost\n\x1b[32;3mCopied to clipboard.\x1b[39;23m\n"
    )
    clipboard_process.assert_called_once()


@pytest.mark.parametrize(
    ("arguments", "expected", "clipboard_failure"),
    [
        ("--copy", "dev", False),
        ("dev -c", "localhost", False),
        ("dev --raw -c", "host: localhost", False),
        ("dev host --raw -c", "host: localhost", False),
        ("dev ssl -c", "verify=true", False),
        ("dev app-services -c", "8000", False),
        ("dev host -c", "localhost", True),
    ],
)
def test_copy_warning_is_dim_yellow_and_follows_output(
    arguments: str,
    expected: str,
    clipboard_failure: bool,
    clipboard_process: Mock,
    mocker: MockerFixture,
) -> None:
    _write_env("dev", {"host": "localhost", "ssl": {"verify": True}})
    if clipboard_failure:
        clipboard_process.side_effect = FileNotFoundError()
    tester = _get_tester()
    output_before_warning = []
    write_error = tester.io.error_output.write_line

    def record_warning(*args, **kwargs) -> None:
        output_before_warning.append(tester.io.fetch_output())
        write_error(*args, **kwargs)

    mocker.patch.object(
        tester.io.error_output, "write_line", side_effect=record_warning,
    )

    tester.execute(arguments, decorated=True)

    assert tester.status_code == 0
    assert len(output_before_warning) == 1
    assert expected in output_before_warning[0]
    assert tester.io.fetch_error().startswith("\x1b[33;2m")


def test_setting_does_not_copy_without_flag(clipboard_process: Mock) -> None:
    _write_env("dev", {"host": "localhost"})
    tester = _get_tester()

    tester.execute("dev host")

    assert tester.io.fetch_output() == "localhost\n"
    clipboard_process.assert_not_called()


@pytest.mark.parametrize(
    "failure",
    [
        FileNotFoundError(),
        subprocess.CalledProcessError(1, "xclip"),
        subprocess.TimeoutExpired("xclip", 5),
    ],
)
def test_setting_reports_clipboard_failure_without_failing_command(
    failure: Exception,
    clipboard_process: Mock,
) -> None:
    clipboard_process.side_effect = failure
    _write_env("dev", {"password": "s3cret"})
    tester = _get_tester()

    tester.execute("dev password -c")

    output = tester.io.fetch_output()
    error = tester.io.fetch_error()
    assert tester.status_code == 0
    assert output == "****\n"
    assert "Could not copy to clipboard" in error
    assert "s3cret" not in error
    assert "Copied to clipboard" not in output


@pytest.mark.parametrize(
    ("session", "command", "encoding"),
    [
        (("linux", False), ["xclip", "-selection", "clipboard"], "utf-8"),
        (("linux", True), ["wl-copy"], "utf-8"),
        (("darwin", False), ["pbcopy"], "utf-8"),
        (("win32", False), ["clip"], "utf-16"),
    ],
)
def test_setting_uses_platform_clipboard(
    session: tuple[str, bool],
    command: list[str],
    encoding: str,
    clipboard_process: Mock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    platform, wayland = session
    monkeypatch.setattr("mlclient.cli.commands.env_show.sys.platform", platform)
    if wayland:
        monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    _write_env("dev", {"password": "żółć"})
    tester = _get_tester()

    tester.execute("dev password -c")

    assert tester.status_code == 0
    clipboard_process.assert_called_once_with(
        command,
        input="żółć".encode(encoding),
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=5,
    )


def test_setting_masks_root_secret() -> None:
    _write_env("dev", {"host": "dev.example.com", "password": "s3cret"})

    tester = _get_tester()
    tester.execute("dev password")

    output = tester.io.fetch_output()
    assert "s3cret" not in output
    assert "****" in output


@pytest.mark.parametrize("flag", ["", "-s", "--secrets"])
def test_setting_copies_unmasked_secret(flag: str, clipboard_process: Mock) -> None:
    _write_env("dev", {"password": "s3cret"})
    tester = _get_tester()

    tester.execute(f"dev password --copy {flag}")

    displayed = "s3cret" if flag else "****"
    assert tester.status_code == 0
    assert tester.io.fetch_output() == f"{displayed}\nCopied to clipboard.\n"
    assert clipboard_process.call_args.kwargs["input"] == b"s3cret"


@pytest.mark.parametrize(
    ("value", "rendered"),
    [({"verify": True}, "verify=true"), (["one", "two"], "one, two"), (None, "-")],
)
def test_setting_ignores_copy_for_non_simple_value(
    value: object,
    rendered: str,
    clipboard_process: Mock,
) -> None:
    _write_env("dev", {"ssl": value})
    tester = _get_tester()

    tester.execute("dev ssl -c")

    assert tester.status_code == 0
    assert tester.io.fetch_output() == f"{rendered}\n"
    assert "only works for simple values" in tester.io.fetch_error()
    clipboard_process.assert_not_called()


@pytest.mark.parametrize("secrets", [False, True])
def test_setting_masks_secrets_in_lists(secrets: bool) -> None:
    items = [{"password": "list-secret"}, [{"api-key": "nested-secret"}]]
    _write_env(
        "dev",
        {"items": items},
    )
    tester = _get_tester()

    tester.execute("dev items" + (" --secrets" if secrets else ""))

    output = tester.io.fetch_output()
    assert tester.status_code == 0
    assert ("list-secret" in output) is secrets
    assert ("nested-secret" in output) is secrets
    assert ("****" in output) is not secrets


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


@pytest.mark.parametrize("secrets", [False, True])
def test_setting_masks_app_server_secrets_in_lists(secrets: bool) -> None:
    items = [{"password": "list-secret"}, [{"api-key": "nested-secret"}]]
    _write_env(
        "dev",
        {"app-servers": [{"id": "rest", "items": items}]},
    )
    tester = _get_tester()

    tester.execute("dev rest" + (" --secrets" if secrets else ""))

    output = tester.io.fetch_output()
    assert tester.status_code == 0
    assert ("list-secret" in output) is secrets
    assert ("nested-secret" in output) is secrets
    assert ("****" in output) is not secrets


@pytest.mark.parametrize(
    ("server_id", "settings"),
    [
        ("app-services", ("8000", "rest", "true")),
        ("manage", ("8002",)),
        ("admin", ("8001",)),
        ("health", ("7997", "auth", "app")),
    ],
)
def test_setting_renders_predefined_app_server_absent_from_file(
    server_id: str,
    settings: tuple[str, ...],
) -> None:
    _write_env("dev", {"host": "dev.example.com"})

    tester = _get_tester()
    tester.execute(f"dev {server_id}")

    output = tester.io.fetch_output()
    assert tester.status_code == 0
    assert server_id in output
    assert all(value in output for value in settings)


@pytest.mark.parametrize("server", ["app-services", "rest"])
def test_setting_ignores_copy_for_app_server(
    server: str, clipboard_process: Mock,
) -> None:
    _write_env("dev", {"app-servers": [{"id": "rest", "port": 8010}]})
    tester = _get_tester()

    tester.execute(f"dev {server} -c")

    output = tester.io.fetch_output()
    assert tester.status_code == 0
    assert server in output
    assert "Setting" in output
    assert "Copied to clipboard" not in output
    assert "only works for simple values" in tester.io.fetch_error()
    clipboard_process.assert_not_called()


def test_setting_prefers_configured_server_over_predefined_default() -> None:
    _write_env("dev", {"app-servers": [{"id": "manage", "port": 9002}]})
    tester = _get_tester()

    tester.execute("dev manage")

    output = tester.io.fetch_output()
    assert tester.status_code == 0
    assert "9002" in output
    assert "8002" not in output


def test_reports_unknown_setting() -> None:
    _write_env("dev", {"host": "dev.example.com"})
    tester = _get_tester()

    with pytest.raises(WrongParametersError) as error:
        tester.execute("dev nope")

    assert "nope" in str(error.value)
