from __future__ import annotations

from pathlib import Path

import pytest
import respx
import yaml
from cleo.testers.command_tester import CommandTester

from mlclient import MLEnvironment
from mlclient.cli import MLCLIentApplication
from mlclient.cli.commands.env_init import (
    _TEMPLATE,
    _client_auth,
    _diff,
    _split_host_port,
)
from mlclient.exceptions import EnvironmentFileExistsError, WrongParametersError
from tests.utils.ml_mockers import MLRespXMocker


@pytest.fixture(autouse=True)
def _work_dir(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _get_tester() -> CommandTester:
    app = MLCLIentApplication()
    return CommandTester(app.find("env init"))


def _written_env(name: str) -> Path:
    return Path.cwd() / ".mlclient" / f"mlclient-{name}.yaml"


def _load_written(name: str) -> dict:
    return yaml.safe_load(_written_env(name).read_text())


def _server(
    name: str,
    port: int,
    *,
    kind: str = "http",
    auth: str = "digest",
    ssl: bool = False,
) -> dict:
    return {
        "name": name,
        "port": port,
        "group": "Default",
        "kind": kind,
        "auth": auth,
        "ssl": ssl,
    }


def _mock_discovery(
    host: str,
    servers: list[dict],
) -> None:
    """Register Manage routes: a server listing and each HTTP server's properties."""
    list_items = [
        {
            "nameref": server["name"],
            "groupnameref": server["group"],
            "kindref": server["kind"],
        }
        for server in servers
    ]
    listing = {"server-default-list": {"list-items": {"list-item": list_items}}}

    mocker = MLRespXMocker(use_router=False)
    mocker.with_url(f"http://{host}:8002/manage/v2/servers")
    mocker.with_request_param("format", "json")
    mocker.with_response_code(200)
    mocker.with_response_content_type("application/json; charset=UTF-8")
    mocker.with_response_body(listing)
    mocker.mock_get()

    for server in servers:
        if server["kind"] != "http":
            continue
        props = {
            "server-name": server["name"],
            "port": server["port"],
            "authentication": server["auth"],
        }
        if server["ssl"]:
            props["ssl-certificate-template"] = "cert-template"
        prop_mocker = MLRespXMocker(use_router=False)
        prop_mocker.with_url(
            f"http://{host}:8002/manage/v2/servers/{server['name']}/properties",
        )
        prop_mocker.with_request_param("group-id", server["group"])
        prop_mocker.with_request_param("format", "json")
        prop_mocker.with_response_code(200)
        prop_mocker.with_response_content_type("application/json; charset=UTF-8")
        prop_mocker.with_response_body(props)
        prop_mocker.mock_get()


# --- template and dispatch ---------------------------------------------------


def test_writes_commented_template_when_only_name_given():
    tester = _get_tester()
    tester.execute("my-env")

    assert tester.status_code == 0
    assert _written_env("my-env").read_text() == _TEMPLATE
    assert "Created" in tester.io.fetch_output()


def test_wizard_prompts_for_name_then_blank_mode_writes_template():
    tester = _get_tester()
    tester.execute("", inputs="my-env\nblank\n")

    assert _written_env("my-env").read_text() == _TEMPLATE


def test_wizard_default_mode_is_blank():
    tester = _get_tester()
    tester.execute("", inputs="my-env\n\n")

    assert _written_env("my-env").read_text() == _TEMPLATE


def test_wizard_reprompts_until_name_is_non_empty():
    tester = _get_tester()
    tester.execute("", inputs="\n   \nmy-env\nblank\n")

    assert _written_env("my-env").read_text() == _TEMPLATE
    assert not _written_env("None").exists()


@respx.mock
def test_from_host_reprompts_on_invalid_port(mocker):
    _mock_discovery("ml.example.com", [_server("scifinder", 3693)])
    mocker.patch("cleo.commands.command.Command.secret", return_value="pw")

    tester = _get_tester()
    tester.execute(
        "prod --from-host=ml.example.com --username=ops",
        inputs="notaport\n8002\n",
    )

    assert _load_written("prod")["host"] == "ml.example.com"


def test_wizard_interactive_flag_runs_wizard_for_named_env():
    tester = _get_tester()
    tester.execute("my-env --interactive", inputs="blank\n")

    assert _written_env("my-env").read_text() == _TEMPLATE


def test_wizard_gradle_mode_derives_from_selector(tmp_path: Path):
    (tmp_path / "gradle-dev.properties").write_text("mlHost=localhost\nmlScheme=http\n")

    tester = _get_tester()
    tester.execute("dev --interactive", inputs="gradle\ndev\n")

    assert MLEnvironment.load_file(_written_env("dev").as_posix())


@respx.mock
def test_wizard_server_mode_discovers_running_instance(mocker):
    _mock_discovery("ml.example.com", [_server("scifinder", 3693)])
    mocker.patch("cleo.commands.command.Command.secret", return_value="pw")

    tester = _get_tester()
    tester.execute("prod --interactive", inputs="server\nml.example.com\n8002\nops\n")

    env = _load_written("prod")
    assert env["host"] == "ml.example.com"
    assert env["username"] == "ops"
    assert env["password"] == "pw"


# --- file handling -----------------------------------------------------------


def test_refuses_to_overwrite_existing_file():
    _written_env("my-env").parent.mkdir()
    _written_env("my-env").write_text("existing")

    tester = _get_tester()
    with pytest.raises(EnvironmentFileExistsError):
        tester.execute("my-env")


def test_force_overwrites_existing_file():
    _written_env("my-env").parent.mkdir()
    _written_env("my-env").write_text("existing")

    tester = _get_tester()
    tester.execute("my-env --force")

    assert _written_env("my-env").read_text() == _TEMPLATE


def test_global_writes_to_home_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))  # noqa: ARG005

    tester = _get_tester()
    tester.execute("my-env --global")

    assert (home / ".mlclient" / "mlclient-my-env.yaml").read_text() == _TEMPLATE


# --- from-gradle -------------------------------------------------------------


def test_from_gradle_derives_name_from_env_selector(tmp_path: Path):
    (tmp_path / "gradle-dev.properties").write_text("mlHost=localhost\nmlScheme=http\n")

    tester = _get_tester()
    tester.execute("--from-gradle=dev")

    assert _written_env("dev").exists()


def test_from_gradle_without_value_prompts_for_name_and_selector(tmp_path: Path):
    (tmp_path / "gradle-dev.properties").write_text("mlHost=localhost\nmlScheme=http\n")

    tester = _get_tester()
    tester.execute("--from-gradle", inputs="myenv\ndev\n")

    assert _written_env("myenv").exists()


def test_from_gradle_prompts_for_name_when_selector_is_a_file(tmp_path: Path):
    props = tmp_path / "gradle.properties"
    props.write_text("mlHost=localhost\nmlScheme=http\n")

    tester = _get_tester()
    tester.execute(f"--from-gradle={props.as_posix()}", inputs="myenv\n")

    assert _written_env("myenv").exists()


def test_from_gradle_forces_name_prompt_with_interactive_flag(tmp_path: Path):
    (tmp_path / "gradle-dev.properties").write_text("mlHost=localhost\nmlScheme=http\n")

    tester = _get_tester()
    tester.execute("--from-gradle=dev -i", inputs="chosen\n")

    assert _written_env("chosen").exists()
    assert not _written_env("dev").exists()


def test_from_gradle_reports_when_no_properties_found():
    tester = _get_tester()
    with pytest.raises(WrongParametersError):
        tester.execute("dev --from-gradle=dev")


def test_from_gradle_comments_out_app_name_when_absent(tmp_path: Path):
    (tmp_path / "gradle-plain.properties").write_text(
        "mlHost=localhost\nmlScheme=http\n",
    )

    tester = _get_tester()
    tester.execute("plain --from-gradle=plain")

    text = _written_env("plain").read_text()
    assert "# app-name:" in text
    assert "app-name" not in _load_written("plain")
    assert MLEnvironment.load_file(_written_env("plain").as_posix())


def test_from_gradle_reports_invalid_properties(tmp_path: Path):
    (tmp_path / "gradle-bad.properties").write_text(
        "mlAppName=demo\nmlCloudApiKey=key-only\n",
    )

    tester = _get_tester()
    with pytest.raises(WrongParametersError):
        tester.execute("bad --from-gradle=bad")


def test_from_gradle_merges_base_and_overlay(tmp_path: Path):
    (tmp_path / "gradle.properties").write_text(
        "mlAppName=demo\n"
        "mlHost=base-host\n"
        "mlUsername=admin\n"
        "mlPassword=secret\n"
        "mlAuthentication=DIGEST\n",
    )
    (tmp_path / "gradle-demo.properties").write_text(
        "mlHost=demo.example.com\n"
        "mlSimpleSsl=true\n"
        "mlAdminSimpleSsl=false\n"
        "mlRestPort=8010\n"
        "mlManageScheme=http\n"
        "mlCloudApiKey=key-123\n"
        "mlCloudBasePath=/ml/instance\n"
        "# a comment\n"
        "! bang comment\n"
        "no-equals-line\n",
    )

    tester = _get_tester()
    tester.execute("demo --from-gradle=demo")

    env = _load_written("demo")
    assert env["app-name"] == "demo"
    assert env["host"] == "demo.example.com"
    assert env["protocol"] == "https"
    assert env["auth"] == "digest"
    assert env["ssl"] == {"verify": False}
    assert env["cloud"] == {"api-key": "key-123", "base-path": "/ml/instance"}
    servers = {server["id"]: server for server in env["app-servers"]}
    assert servers["rest"] == {"id": "rest", "port": 8010, "rest": True}
    assert servers["manage"] == {"id": "manage", "protocol": "http"}
    assert servers["admin"] == {"id": "admin", "protocol": "http"}
    assert MLEnvironment.load_file(_written_env("demo").as_posix())


def test_from_gradle_reads_a_file_path(tmp_path: Path):
    props = tmp_path / "custom.properties"
    props.write_text("mlAppName=plain\nmlHost=localhost\nmlScheme=http\n")

    tester = _get_tester()
    tester.execute(f"plain --from-gradle={props.as_posix()}")

    env = _load_written("plain")
    assert env["app-name"] == "plain"
    assert env["protocol"] == "http"
    assert "app-servers" not in env
    assert "ssl" not in env
    assert "cloud" not in env


# --- from-host: connection ---------------------------------------------------


@respx.mock
def test_from_host_without_value_prompts_for_all_connection_fields(mocker):
    _mock_discovery("ml.example.com", [_server("scifinder", 3693)])
    mocker.patch("cleo.commands.command.Command.secret", return_value="pw")

    tester = _get_tester()
    tester.execute("--from-host", inputs="prod\nml.example.com\n8002\nops\n")

    env = _load_written("prod")
    assert env["host"] == "ml.example.com"
    assert env["username"] == "ops"
    assert env["password"] == "pw"
    assert env["protocol"] == "http"
    assert env["auth"] == "digest"


@respx.mock
def test_from_host_prompts_for_name_when_omitted():
    _mock_discovery("ml.example.com", [_server("scifinder", 3693)])

    tester = _get_tester()
    tester.execute(
        "--from-host=ml.example.com:8002 --username=ops --password=pw",
        inputs="prod\n",
    )

    assert _load_written("prod")["host"] == "ml.example.com"


@respx.mock
def test_from_host_prompts_for_username_and_password_when_omitted(mocker):
    _mock_discovery("localhost", [_server("scifinder", 3693)])
    mocker.patch("cleo.commands.command.Command.secret", return_value="secret")

    tester = _get_tester()
    tester.execute("prod --from-host=localhost:8002", inputs="admin\n")

    env = _load_written("prod")
    assert env["username"] == "admin"
    assert env["password"] == "secret"


@respx.mock
def test_from_host_resolves_without_prompting_when_fully_specified():
    _mock_discovery("ml.example.com", [_server("scifinder", 3693)])

    tester = _get_tester()
    tester.execute("prod --from-host=ml.example.com --username=ops --password=pw")

    env = _load_written("prod")
    assert env["host"] == "ml.example.com"
    assert env["username"] == "ops"
    assert env["password"] == "pw"


@respx.mock
def test_from_host_honours_username_and_password_options():
    _mock_discovery("ml.example.com", [_server("scifinder", 3693)])

    tester = _get_tester()
    tester.execute("prod --from-host=ml.example.com --username=ops --password=pw")

    env = _load_written("prod")
    assert env["host"] == "ml.example.com"
    assert env["username"] == "ops"
    assert env["password"] == "pw"


@respx.mock
def test_from_host_produces_a_loadable_environment():
    _mock_discovery("localhost", [_server("scifinder", 3693)])

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    assert MLEnvironment.load_file(_written_env("prod").as_posix())


@respx.mock
def test_from_host_honours_auth_option():
    _mock_discovery("ml.example.com", [_server("scifinder", 3693)])

    tester = _get_tester()
    tester.execute(
        "prod --from-host=ml.example.com --username=ops --password=pw --auth=basic",
    )

    assert _load_written("prod")["auth"] == "basic"


@respx.mock
def test_from_host_defaults_auth_to_digest():
    _mock_discovery("ml.example.com", [_server("scifinder", 3693)])

    tester = _get_tester()
    tester.execute("prod --from-host=ml.example.com --username=ops --password=pw")

    assert _load_written("prod")["auth"] == "digest"


def test_from_host_rejects_unsupported_auth():
    tester = _get_tester()
    with pytest.raises(WrongParametersError):
        tester.execute(
            "prod --from-host=ml.example.com --username=ops "
            "--password=pw --auth=kerberos",
        )


# --- from-host: app-name label -----------------------------------------------


@respx.mock
def test_from_host_writes_app_name_when_provided():
    _mock_discovery("localhost", [_server("scifinder", 3693)])

    tester = _get_tester()
    tester.execute(
        "prod --from-host=localhost --username=admin "
        "--password=pw --app-name=scifinder",
    )

    assert _load_written("prod")["app-name"] == "scifinder"


@respx.mock
def test_from_host_comments_out_app_name_when_absent():
    _mock_discovery("localhost", [_server("scifinder", 3693)])

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    assert "# app-name:" in _written_env("prod").read_text()
    assert "app-name" not in _load_written("prod")


# --- from-host: server filtering ---------------------------------------------


@respx.mock
def test_from_host_filters_servers_by_app_name():
    _mock_discovery(
        "localhost",
        [_server("scifinder", 3693), _server("other-app", 4000)],
    )

    tester = _get_tester()
    tester.execute(
        "prod --from-host=localhost --username=admin "
        "--password=pw --app-name=scifinder",
    )

    env = _load_written("prod")
    assert env["app-servers"] == [{"id": "scifinder", "port": 3693, "rest": True}]


@respx.mock
def test_from_host_keeps_all_servers_when_app_name_matches_none():
    _mock_discovery(
        "localhost",
        [_server("alpha", 3693), _server("beta", 4000)],
    )

    tester = _get_tester()
    tester.execute(
        "prod --from-host=localhost --username=admin --password=pw --app-name=nomatch",
    )

    env = _load_written("prod")
    assert [server["id"] for server in env["app-servers"]] == ["alpha", "beta"]


@respx.mock
def test_from_host_keeps_all_servers_when_app_name_absent():
    _mock_discovery(
        "localhost",
        [_server("alpha", 3693), _server("beta", 4000)],
    )

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    env = _load_written("prod")
    assert [server["id"] for server in env["app-servers"]] == ["alpha", "beta"]


# --- from-host: manage / admin tiers -----------------------------------------


@respx.mock
def test_from_host_omits_manage_and_admin_when_consistent_with_root():
    _mock_discovery(
        "localhost",
        [
            _server("scifinder", 3693),
            _server("Manage", 8002),
            _server("Admin", 8001),
        ],
    )

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    env = _load_written("prod")
    assert env["app-servers"] == [{"id": "scifinder", "port": 3693, "rest": True}]


@respx.mock
def test_from_host_emits_manage_when_auth_diverges():
    _mock_discovery("localhost", [_server("Manage", 8002, auth="basic")])

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    assert _load_written("prod")["app-servers"] == [{"id": "manage", "auth": "basic"}]


@respx.mock
def test_from_host_emits_admin_when_auth_diverges():
    _mock_discovery("localhost", [_server("Admin", 8001, auth="basic")])

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    assert _load_written("prod")["app-servers"] == [{"id": "admin", "auth": "basic"}]


@respx.mock
def test_from_host_emits_manage_when_protocol_diverges():
    _mock_discovery("localhost", [_server("Manage", 8002, ssl=True)])

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    env = _load_written("prod")
    assert env["app-servers"] == [{"id": "manage", "protocol": "https"}]


# --- from-host: protocol and server kind -------------------------------------


@respx.mock
def test_from_host_emits_protocol_for_ssl_server():
    _mock_discovery("localhost", [_server("scifinder", 3693, ssl=True)])

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    env = _load_written("prod")
    assert env["app-servers"] == [
        {"id": "scifinder", "port": 3693, "rest": True, "protocol": "https"},
    ]


@respx.mock
def test_from_host_ignores_non_http_servers():
    _mock_discovery(
        "localhost",
        [_server("scifinder", 3693), _server("xdbc-server", 3700, kind="xdbc")],
    )

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    env = _load_written("prod")
    assert env["app-servers"] == [{"id": "scifinder", "port": 3693, "rest": True}]


@respx.mock
def test_from_host_omits_app_servers_when_no_http_server_found():
    _mock_discovery("localhost", [_server("xdbc-server", 3700, kind="xdbc")])

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    assert "app-servers" not in _load_written("prod")


# --- module helpers ----------------------------------------------------------


def test_split_host_port_defaults_to_manage_port():
    assert _split_host_port("localhost") == ("localhost", 8002)


def test_split_host_port_reads_explicit_port():
    assert _split_host_port("localhost:9000") == ("localhost", 9000)


@pytest.mark.parametrize(
    ("server_auth", "expected"),
    [
        (None, "digest"),
        ("basic", "basic"),
        ("DIGEST", "digest"),
        ("kerberos-ticket", "kerberos"),
        ("application-level", "digest"),
        ("unknown-scheme", "digest"),
    ],
)
def test_client_auth_maps_server_scheme(server_auth, expected):
    assert _client_auth(server_auth) == expected


def test_diff_returns_none_when_equal():
    assert _diff("http", "http") is None


def test_diff_returns_value_when_different():
    assert _diff("https", "http") == "https"
