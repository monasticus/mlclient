from __future__ import annotations

from pathlib import Path

import pytest
import respx
import yaml
from cleo.testers.command_tester import CommandTester

from mlclient import MLEnvironment
from mlclient.cli import MLCLIentApplication
from mlclient.cli.commands.init_env import (
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
    return CommandTester(app.find("init env"))


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


def test_wizard_without_name_is_not_implemented():
    tester = _get_tester()
    with pytest.raises(NotImplementedError):
        tester.execute("")


def test_wizard_with_interactive_flag_is_not_implemented():
    tester = _get_tester()
    with pytest.raises(NotImplementedError):
        tester.execute("my-env --interactive")


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


def test_from_gradle_requires_a_name():
    tester = _get_tester()
    with pytest.raises(WrongParametersError):
        tester.execute("--from-gradle=dev")


def test_from_gradle_reports_when_no_properties_found():
    tester = _get_tester()
    with pytest.raises(WrongParametersError):
        tester.execute("dev --from-gradle=dev")


def test_from_gradle_rejects_properties_without_app_name(tmp_path: Path):
    (tmp_path / "gradle-bad.properties").write_text("mlHost=localhost\n")

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


# --- from-host ---------------------------------------------------------------


def test_from_host_requires_a_name():
    tester = _get_tester()
    with pytest.raises(WrongParametersError):
        tester.execute("--from-host=localhost")


@respx.mock
def test_from_host_defaults_username_and_prompts_for_password(mocker):
    _mock_discovery("localhost", [_server("scifinder", 3693)])
    mocker.patch(
        "cleo.commands.command.Command.secret",
        return_value="secret",
    )

    tester = _get_tester()
    tester.execute("scifinder --from-host=localhost")

    env = _load_written("scifinder")
    assert env["app-name"] == "scifinder"
    assert env["host"] == "localhost"
    assert env["username"] == "admin"
    assert env["password"] == "secret"
    assert env["protocol"] == "http"
    assert env["auth"] == "digest"
    assert env["app-servers"] == [{"id": "scifinder", "port": 3693, "rest": True}]


@respx.mock
def test_from_host_honours_username_and_password_options():
    _mock_discovery("ml.example.com", [_server("scifinder", 3693)])

    tester = _get_tester()
    tester.execute("scifinder --from-host=ml.example.com --username=ops --password=pw")

    env = _load_written("scifinder")
    assert env["host"] == "ml.example.com"
    assert env["username"] == "ops"
    assert env["password"] == "pw"


@respx.mock
def test_from_host_keeps_only_servers_matching_the_name():
    _mock_discovery(
        "localhost",
        [_server("scifinder", 3693), _server("other-app", 4000)],
    )

    tester = _get_tester()
    tester.execute("scifinder --from-host=localhost --password=pw")

    env = _load_written("scifinder")
    assert env["app-servers"] == [{"id": "scifinder", "port": 3693, "rest": True}]


@respx.mock
def test_from_host_keeps_all_servers_when_name_matches_none():
    _mock_discovery(
        "localhost",
        [_server("alpha", 3693), _server("beta", 4000)],
    )

    tester = _get_tester()
    tester.execute("zzz --from-host=localhost --password=pw")

    env = _load_written("zzz")
    assert [server["id"] for server in env["app-servers"]] == ["alpha", "beta"]


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
    tester.execute("zzz --from-host=localhost --password=pw")

    env = _load_written("zzz")
    assert env["app-servers"] == [{"id": "scifinder", "port": 3693, "rest": True}]


@respx.mock
def test_from_host_emits_manage_when_auth_diverges():
    _mock_discovery(
        "localhost",
        [_server("Manage", 8002, auth="basic")],
    )

    tester = _get_tester()
    tester.execute("zzz --from-host=localhost --password=pw")

    env = _load_written("zzz")
    assert env["app-servers"] == [{"id": "manage", "auth": "basic"}]


@respx.mock
def test_from_host_emits_protocol_for_ssl_server():
    _mock_discovery(
        "localhost",
        [_server("scifinder", 3693, ssl=True)],
    )

    tester = _get_tester()
    tester.execute("scifinder --from-host=localhost --password=pw")

    env = _load_written("scifinder")
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
    tester.execute("zzz --from-host=localhost --password=pw")

    env = _load_written("zzz")
    assert env["app-servers"] == [{"id": "scifinder", "port": 3693, "rest": True}]


@respx.mock
def test_from_host_omits_app_servers_when_no_http_server_found():
    _mock_discovery("localhost", [_server("xdbc-server", 3700, kind="xdbc")])

    tester = _get_tester()
    tester.execute("zzz --from-host=localhost --password=pw")

    env = _load_written("zzz")
    assert "app-servers" not in env


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
