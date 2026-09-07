from __future__ import annotations

import base64
import shlex
from pathlib import Path

import httpx
import pytest
import respx
import yaml
from cleo.testers.command_tester import CommandTester

from mlclient import MLEnvironment
from mlclient.cli import MLCLIentApplication
from mlclient.cli.commands.env_init import _TEMPLATE
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
    **kwargs,
) -> dict:
    return {
        "name": name,
        "port": port,
        "group": "Default",
        "kind": "http",
        "auth": "digest",
        "ssl": False,
        "rest": True,
        **kwargs,
    }


def _mock_discovery(
    host: str,
    servers: list[dict],
    manage_port: int = 8002,
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
    mocker.with_url(f"http://{host}:{manage_port}/manage/v2/servers")
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
            "url-rewriter": (
                "/MarkLogic/rest-api/rewriter.xml" if server["rest"] else ""
            ),
        }
        if server["auth"] is not None:
            props["authentication"] = server["auth"]
        if server["ssl"]:
            props["ssl-certificate-template"] = "cert-template"
        mocker.with_url(
            f"http://{host}:{manage_port}/manage/v2/servers/"
            f"{server['name']}/properties",
        )
        mocker.with_request_param("group-id", server["group"])
        mocker.with_request_param("format", "json")
        mocker.with_response_code(200)
        mocker.with_response_content_type("application/json; charset=UTF-8")
        mocker.with_response_body(props)
        mocker.mock_get()


# --- dispatch ----------------------------------------------------------------


def test_wizard_default_mode_is_blank():
    tester = _get_tester()
    tester.execute("", inputs="my-env\n\n")

    assert _written_env("my-env").read_text() == _TEMPLATE


def test_wizard_reprompts_until_name_is_non_empty():
    tester = _get_tester()
    tester.execute("", inputs="\n   \nmy-env\nblank\n")

    assert _written_env("my-env").read_text() == _TEMPLATE
    assert not _written_env("None").exists()


def test_wizard_interactive_flag_runs_wizard_for_named_env():
    tester = _get_tester()
    tester.execute("my-env --interactive", inputs="blank\n")

    assert _written_env("my-env").read_text() == _TEMPLATE


def test_handle_rejects_both_from_host_and_from_gradle(tmp_path: Path):
    (tmp_path / "gradle-dev.properties").write_text(
        "mlHost=gradle-host\nmlScheme=http\n",
    )

    tester = _get_tester()
    with pytest.raises(WrongParametersError) as err:
        tester.execute("prod --from-host=host-host --from-gradle=dev")

    assert "--from-host" in err.value.args[0]
    assert "--from-gradle" in err.value.args[0]
    assert not _written_env("prod").exists()


# --- blank -------------------------------------------------------------------


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


# --- file handling -----------------------------------------------------------


def test_refuses_to_overwrite_existing_file():
    _written_env("my-env").parent.mkdir()
    _written_env("my-env").write_text("existing")

    tester = _get_tester()
    with pytest.raises(EnvironmentFileExistsError) as err:
        tester.execute("my-env")

    message = err.value.args[0]
    assert _written_env("my-env").as_posix() in message
    assert "--force" in message


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
    monkeypatch.setattr(Path, "home", classmethod(lambda _cls: home))

    tester = _get_tester()
    tester.execute("my-env --global")

    assert (home / ".mlclient" / "mlclient-my-env.yaml").read_text() == _TEMPLATE


# --- gradle ------------------------------------------------------------------


def test_wizard_gradle_mode_derives_from_selector(tmp_path: Path):
    (tmp_path / "gradle-dev.properties").write_text("mlHost=localhost\nmlScheme=http\n")

    tester = _get_tester()
    tester.execute("dev --interactive", inputs="gradle\ndev\n")

    assert MLEnvironment.load_file(_written_env("dev").as_posix())


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


def test_from_gradle_writes_app_auth(tmp_path: Path):
    (tmp_path / "gradle-app.properties").write_text(
        "mlAuthentication=application-level\n"
        "mlRestPort=8010\n"
        "mlRestAuthentication=application-level\n",
    )

    tester = _get_tester()
    tester.execute("app --from-gradle=app")

    env = _load_written("app")
    assert env["auth"] == "app"
    assert env["app-servers"][0]["auth"] == "app"
    config = MLEnvironment.load_file(_written_env("app").as_posix())
    assert config.auth is None
    assert config.provide_config("rest").auth is None


def test_from_gradle_reads_a_file_path(tmp_path: Path):
    props = tmp_path / "custom.properties"
    props.write_text("mlAppName=plain\nmlHost=localhost\nmlScheme=http\n")

    tester = _get_tester()
    tester.execute(f"plain --from-gradle={props.as_posix()}")

    env = _load_written("plain")
    assert env["app-name"] == "plain"
    assert env["protocol"] == "http"
    assert "auth" not in env
    assert "app-servers" not in env
    assert "ssl" not in env
    assert "cloud" not in env


def test_from_gradle_writes_rest_server_credentials(tmp_path: Path):
    (tmp_path / "gradle-rest.properties").write_text(
        "mlHost=localhost\nmlScheme=http\n"
        "mlRestPort=8010\n"
        "mlRestAdminUsername=rest-admin\n"
        "mlRestAdminPassword=rest-secret\n",
    )

    tester = _get_tester()
    tester.execute("rest --from-gradle=rest")

    servers = {server["id"]: server for server in _load_written("rest")["app-servers"]}
    assert servers["rest"]["username"] == "rest-admin"
    assert servers["rest"]["password"] == "rest-secret"
    assert MLEnvironment.load_file(_written_env("rest").as_posix())


def test_from_gradle_emits_app_services_override(tmp_path: Path):
    (tmp_path / "gradle-appsvc.properties").write_text(
        "mlHost=localhost\nmlScheme=http\n"
        "mlAppServicesPort=8000\n"
        "mlAppServicesAuthentication=basic\n",
    )

    tester = _get_tester()
    tester.execute("appsvc --from-gradle=appsvc")

    servers = {
        server["id"]: server for server in _load_written("appsvc")["app-servers"]
    }
    assert servers["app-services"]["auth"] == "basic"
    assert servers["app-services"]["port"] == 8000


def test_from_gradle_root_protocol_https_from_scheme(tmp_path: Path):
    (tmp_path / "gradle-https.properties").write_text(
        "mlHost=localhost\nmlScheme=https\n",
    )

    tester = _get_tester()
    tester.execute("https --from-gradle=https")

    env = _load_written("https")
    assert env["protocol"] == "https"
    assert "ssl" not in env


def test_from_gradle_emits_rest_protocol_when_divergent(tmp_path: Path):
    (tmp_path / "gradle-restssl.properties").write_text(
        "mlHost=localhost\nmlScheme=http\n"
        "mlRestPort=8010\n"
        "mlRestSimpleSsl=true\n",
    )

    tester = _get_tester()
    tester.execute("restssl --from-gradle=restssl")

    servers = {
        server["id"]: server for server in _load_written("restssl")["app-servers"]
    }
    assert servers["rest"]["protocol"] == "https"


def test_from_gradle_ssl_verify_from_non_root_simple_ssl(tmp_path: Path):
    (tmp_path / "gradle-nrssl.properties").write_text(
        "mlHost=localhost\nmlScheme=http\n"
        "mlRestPort=8010\n"
        "mlRestSimpleSsl=true\n",
    )

    tester = _get_tester()
    tester.execute("nrssl --from-gradle=nrssl")

    assert _load_written("nrssl")["ssl"] == {"verify": False}


# --- host: connection --------------------------------------------------------


@respx.mock
def test_from_host_without_value_prompts_for_all_connection_fields(mocker):
    _mock_discovery("ml.example.com", [_server("my-app", 8010)])
    mocker.patch("cleo.commands.command.Command.secret", return_value="pw")

    tester = _get_tester()
    tester.execute(
        "--from-host",
        inputs="prod\nml.example.com\n8002\nops\n\n",
    )

    env = _load_written("prod")
    assert env["host"] == "ml.example.com"
    assert env["username"] == "ops"
    assert env["password"] == "pw"
    assert env["protocol"] == "http"
    assert env["auth"] == "digest"


@respx.mock
def test_from_host_prompts_for_name_when_omitted():
    _mock_discovery("ml.example.com", [_server("my-app", 8010)])

    tester = _get_tester()
    tester.execute(
        "--from-host=ml.example.com:8002 --username=ops --password=pw",
        inputs="prod\n\n",
    )

    assert _load_written("prod")["host"] == "ml.example.com"


@respx.mock
def test_wizard_server_mode_discovers_running_instance(mocker):
    _mock_discovery("ml.example.com", [_server("my-app", 8010)])
    mocker.patch("cleo.commands.command.Command.secret", return_value="pw")

    tester = _get_tester()
    tester.execute(
        "prod --interactive",
        inputs="server\nml.example.com\n8002\nops\nbasic\n",
    )

    env = _load_written("prod")
    assert env["host"] == "ml.example.com"
    assert env["username"] == "ops"
    assert env["password"] == "pw"
    assert "Connecting to http://ml.example.com:8002..." in tester.io.fetch_output()
    assert env["auth"] == "basic"


@pytest.mark.parametrize(
    ("arguments", "inputs"),
    [("prod --interactive", "server\n\n\n\n0\n"), ("", "prod\nserver\n\n\n\n0\n")],
)
@respx.mock
def test_wizard_server_mode_accepts_default_password(mocker, arguments, inputs):
    _mock_discovery("localhost", [_server("my-app", 8010)])
    mocker.patch("cleo.ui.question.getpass.getpass", return_value="")

    tester = _get_tester()
    tester.execute(arguments, inputs=inputs)

    assert _load_written("prod")["password"] == "admin"
    assert _load_written("prod")["auth"] == "basic"
    assert "Connecting to http://localhost:8002..." in tester.io.fetch_output()


@respx.mock
def test_from_host_reprompts_on_invalid_port(mocker):
    _mock_discovery("ml.example.com", [_server("my-app", 8010)])
    mocker.patch("cleo.commands.command.Command.secret", return_value="pw")

    tester = _get_tester()
    tester.execute(
        "prod --from-host=ml.example.com --username=ops --interactive",
        inputs="notaport\n8002\n\n",
    )

    assert _load_written("prod")["host"] == "ml.example.com"


@respx.mock
def test_from_host_with_name_defaults_username_and_password():
    _mock_discovery("localhost", [_server("my-app", 8010)])

    tester = _get_tester()
    tester.execute("prod --from-host=localhost")

    env = _load_written("prod")
    assert env["username"] == "admin"
    assert env["password"] == "admin"
    assert env["auth"] == "digest"
    assert "Connecting to http://localhost:8002..." in tester.io.fetch_output()


@respx.mock
def test_from_host_with_name_and_no_value_uses_all_defaults():
    _mock_discovery("localhost", [_server("my-app", 8010)])

    tester = _get_tester()
    tester.execute("prod --from-host")

    env = _load_written("prod")
    assert env["host"] == "localhost"
    assert env["username"] == "admin"
    assert env["password"] == "admin"
    assert env["auth"] == "digest"


@respx.mock
def test_from_host_uses_explicit_port():
    _mock_discovery("ml.example.com", [_server("my-app", 8010)], manage_port=9000)

    tester = _get_tester()
    tester.execute("prod --from-host=ml.example.com:9000")

    assert "Connecting to http://ml.example.com:9000..." in tester.io.fetch_output()


@pytest.mark.parametrize(
    "host",
    ["ml.example.com:not-a-port", "ml.example.com:0", "ml.example.com:65536"],
)
def test_from_host_rejects_invalid_explicit_port(host):
    tester = _get_tester()

    with pytest.raises(WrongParametersError, match="Port must be"):
        tester.execute(f"prod --from-host={host}")


def test_from_host_rejects_empty_host():
    tester = _get_tester()

    with pytest.raises(WrongParametersError, match="requires a host name"):
        tester.execute("prod --from-host=:9000")


@respx.mock
def test_from_host_interactive_prompts_only_for_missing_options(mocker):
    _mock_discovery("ml.example.com", [_server("my-app", 8010)], manage_port=9000)
    mocker.patch("cleo.commands.command.Command.secret", return_value="secret")

    tester = _get_tester()
    tester.execute(
        "prod --from-host=ml.example.com:9000 --username=ops --interactive",
        inputs="basic\n",
    )

    env = _load_written("prod")
    assert env["host"] == "ml.example.com"
    assert env["username"] == "ops"
    assert env["password"] == "secret"
    assert env["auth"] == "basic"


@respx.mock
def test_from_host_resolves_without_prompting_when_fully_specified():
    _mock_discovery("ml.example.com", [_server("my-app", 8010)])

    tester = _get_tester()
    tester.execute("prod --from-host=ml.example.com --username=ops --password=pw")

    env = _load_written("prod")
    assert env["host"] == "ml.example.com"
    assert env["username"] == "ops"
    assert env["password"] == "pw"


@respx.mock
def test_from_host_honours_username_and_password_options():
    _mock_discovery("ml.example.com", [_server("my-app", 8010)])

    tester = _get_tester()
    tester.execute("prod --from-host=ml.example.com --username=ops --password=pw")

    env = _load_written("prod")
    assert env["host"] == "ml.example.com"
    assert env["username"] == "ops"
    assert env["password"] == "pw"


@respx.mock
def test_from_host_produces_a_loadable_environment():
    _mock_discovery("localhost", [_server("my-app", 8010)])

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    assert MLEnvironment.load_file(_written_env("prod").as_posix())


@respx.mock
def test_from_host_honours_auth_option():
    _mock_discovery("ml.example.com", [_server("my-app", 8010)])

    tester = _get_tester()
    tester.execute(
        "prod --from-host=ml.example.com --username=ops --password=pw --auth=basic",
    )

    assert _load_written("prod")["auth"] == "basic"


@respx.mock
def test_from_host_defaults_auth_to_digest():
    _mock_discovery("ml.example.com", [_server("my-app", 8010)])

    tester = _get_tester()
    tester.execute("prod --from-host=ml.example.com --username=ops --password=pw")

    assert _load_written("prod")["auth"] == "digest"


@respx.mock
def test_from_host_normalizes_uppercase_auth():
    _mock_discovery("ml.example.com", [_server("my-app", 8010)])

    tester = _get_tester()
    tester.execute(
        "prod --from-host=ml.example.com --username=ops --password=pw --auth=BASIC",
    )

    assert _load_written("prod")["auth"] == "basic"


def test_from_host_rejects_unsupported_auth():
    tester = _get_tester()
    with pytest.raises(WrongParametersError):
        tester.execute(
            "prod --from-host=ml.example.com --username=ops "
            "--password=pw --auth=kerberos",
        )


@pytest.mark.parametrize(
    ("arguments", "inputs"),
    [
        ("local --from-host=localhost:8002", ""),
        ("local --from-host=localhost:8002 -i", ""),
        ("-i", "local\nserver\n\n\n"),
    ],
)
@pytest.mark.parametrize("password", ["", "app-servers:\nsecret"])
@respx.mock
def test_from_host_preserves_explicit_credentials_on_wire(arguments, inputs, password):
    credentials = base64.b64encode(f"reader:{password}".encode()).decode()
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/servers")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_header("Authorization", f"Basic {credentials}")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(
        {
            "server-default-list": {"list-items": {"list-item": []}},
        },
    )
    ml_mocker.mock_get()

    tester = _get_tester()
    tester.execute(
        f"{arguments} --username=reader --password={shlex.quote(password)}"
        " --auth=basic",
        inputs=inputs,
    )

    env = _load_written("local")
    assert env["username"] == "reader"
    assert env["password"] == password
    assert env["auth"] == "basic"
    output = tester.io.fetch_output()
    assert "Password [" not in output
    assert "Username [" not in output
    assert "Auth [" not in output
    assert "Connecting to http://localhost:8002..." in output


# --- host: app-name label ----------------------------------------------------


@respx.mock
def test_from_host_writes_app_name_when_provided():
    _mock_discovery("localhost", [_server("my-app", 8010)])

    tester = _get_tester()
    tester.execute(
        "prod --from-host=localhost --username=admin "
        "--password=pw --app-name=my-app",
    )

    assert _load_written("prod")["app-name"] == "my-app"


@respx.mock
def test_from_host_comments_out_app_name_when_absent():
    _mock_discovery("localhost", [_server("my-app", 8010)])

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    assert "# app-name:" in _written_env("prod").read_text()
    assert "app-name" not in _load_written("prod")


# --- host: server filtering --------------------------------------------------


@respx.mock
def test_from_host_filters_servers_by_app_name():
    _mock_discovery(
        "localhost",
        [_server("my-app", 8010), _server("other-app", 4000)],
    )

    tester = _get_tester()
    tester.execute(
        "prod --from-host=localhost --username=admin "
        "--password=pw --app-name=my-app",
    )

    env = _load_written("prod")
    assert env["app-servers"] == [{"id": "my-app", "port": 8010, "rest": True}]


@respx.mock
def test_wizard_server_mode_filters_by_app_name(mocker):
    _mock_discovery(
        "ml.example.com",
        [_server("my-app", 8010), _server("other-app", 4000)],
    )
    mocker.patch("cleo.commands.command.Command.secret", return_value="pw")

    tester = _get_tester()
    tester.execute(
        "prod --interactive --app-name=my-app",
        inputs="server\nml.example.com\n8002\nops\ndigest\n",
    )

    env = _load_written("prod")
    assert env["app-name"] == "my-app"
    assert env["app-servers"] == [{"id": "my-app", "port": 8010, "rest": True}]


@respx.mock
def test_from_host_keeps_all_servers_when_app_name_matches_none():
    _mock_discovery(
        "localhost",
        [_server("alpha", 8010), _server("beta", 4000)],
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
        [_server("alpha", 8010), _server("beta", 4000)],
    )

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    env = _load_written("prod")
    assert [server["id"] for server in env["app-servers"]] == ["alpha", "beta"]


# --- host: manage / admin tiers ----------------------------------------------


@respx.mock
def test_from_host_omits_manage_and_admin_when_consistent_with_root():
    _mock_discovery(
        "localhost",
        [
            _server("my-app", 8010),
            _server("Manage", 8002),
            _server("Admin", 8001),
        ],
    )

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    env = _load_written("prod")
    assert env["app-servers"] == [{"id": "my-app", "port": 8010, "rest": True}]


@respx.mock
def test_from_host_omits_default_app_services_and_documents_defaults():
    healthcheck = _server("HealthCheck", 7997, auth="application-level", rest=False)
    _mock_discovery(
        "localhost",
        [_server("App-Services", 8000), healthcheck],
    )

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    env = _load_written("prod")
    assert "app-servers" not in env
    health = MLEnvironment.load_file(
        _written_env("prod").as_posix(),
    ).provide_config("health")
    assert health.port == 7997
    assert health.auth is None
    assert (
        "app-services (8000, REST), manage (8002), admin (8001), "
        "health (7997, app)"
        in _written_env(
            "prod",
        ).read_text()
    )


@respx.mock
def test_from_host_emits_lowercase_app_services_override():
    _mock_discovery("localhost", [_server("App-Services", 8000, auth="basic")])

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    assert _load_written("prod")["app-servers"] == [
        {"id": "app-services", "auth": "basic", "rest": True},
    ]


@respx.mock
def test_from_host_emits_manage_when_auth_diverges():
    _mock_discovery("localhost", [_server("Manage", 8002, auth="basic")])

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    assert _load_written("prod")["app-servers"] == [
        {"id": "manage", "port": 8002, "auth": "basic"},
    ]


@respx.mock
def test_from_host_emits_admin_when_auth_diverges():
    _mock_discovery("localhost", [_server("Admin", 8001, auth="basic")])

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    assert _load_written("prod")["app-servers"] == [
        {"id": "admin", "port": 8001, "auth": "basic"},
    ]


@respx.mock
def test_from_host_emits_manage_when_protocol_diverges():
    _mock_discovery("localhost", [_server("Manage", 8002, ssl=True)])

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    env = _load_written("prod")
    assert env["app-servers"] == [
        {"id": "manage", "port": 8002, "protocol": "https"},
    ]


# --- host: protocol and server kind ------------------------------------------


@pytest.mark.parametrize(
    "server",
    [
        ("HealthCheck", 7997, "basic", False, "http", "health"),
        ("HealthCheck", 7997, "application-level", False, "https", "health"),
        ("HealthCheck", 7997, "application-level", True, "http", "health"),
        ("Manage", 8002, "basic", False, "http", "manage"),
        ("Admin", 8001, "basic", False, "http", "admin"),
        ("App-Services", 8000, "digest", False, "http", "app-services"),
        ("content", 8010, "application-level", False, "http", "content"),
        ("content", 8010, "digest", True, "http", "content"),
    ],
)
@respx.mock
def test_from_host_preserves_discovered_connection(server):
    name, port, auth, rest, protocol, identifier = server
    ml_mocker = MLRespXMocker(use_router=False)
    ml_mocker.with_url("http://localhost:8002/manage/v2/servers")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(
        {
            "server-default-list": {
                "list-items": {
                    "list-item": [
                        {"nameref": name, "groupnameref": "Default", "kindref": "http"},
                    ],
                },
            },
        },
    )
    ml_mocker.mock_get()
    ml_mocker.with_url(f"http://localhost:8002/manage/v2/servers/{name}/properties")
    ml_mocker.with_request_param("format", "json")
    ml_mocker.with_request_param("group-id", "Default")
    ml_mocker.with_response_code(200)
    ml_mocker.with_response_body(
        {
            "server-name": name,
            "port": port,
            "authentication": auth,
            "url-rewriter": "/MarkLogic/rest-api/rewriter.xml" if rest else "",
            "ssl-certificate-template": "cert-template" if protocol == "https" else "",
        },
    )
    ml_mocker.mock_get()

    tester = _get_tester()
    tester.execute("local --from-host=localhost")

    env = MLEnvironment.load_file(_written_env("local").as_posix())
    config = env.provide_config(identifier)
    assert config.port == port
    assert config.protocol == protocol
    assert (identifier in env.rest_servers) is rest
    if auth == "application-level":
        assert config.auth is None
    else:
        expected = httpx.BasicAuth if auth == "basic" else httpx.DigestAuth
        assert isinstance(config.auth, expected)


@respx.mock
def test_from_host_emits_protocol_for_ssl_server():
    _mock_discovery("localhost", [_server("my-app", 8010, ssl=True)])

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    env = _load_written("prod")
    assert env["app-servers"] == [
        {"id": "my-app", "port": 8010, "rest": True, "protocol": "https"},
    ]


@respx.mock
def test_from_host_omits_default_health_server():
    healthcheck = _server("HealthCheck", 7997, auth="application-level", rest=False)
    _mock_discovery(
        "localhost",
        [healthcheck],
    )

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    assert "app-servers" not in _load_written("prod")


@respx.mock
def test_from_host_emits_health_auth_override():
    healthcheck = _server("HealthCheck", 7997, auth="basic", rest=False)
    _mock_discovery("localhost", [healthcheck])

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    assert _load_written("prod")["app-servers"] == [
        {"id": "health", "port": 7997, "auth": "basic"},
    ]


@respx.mock
def test_from_host_ignores_non_http_servers():
    _mock_discovery(
        "localhost",
        [_server("my-app", 8010), _server("xdbc-server", 3700, kind="xdbc")],
    )

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    env = _load_written("prod")
    assert env["app-servers"] == [{"id": "my-app", "port": 8010, "rest": True}]


@respx.mock
def test_from_host_omits_app_servers_when_no_http_server_found():
    _mock_discovery("localhost", [_server("xdbc-server", 3700, kind="xdbc")])

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    assert "app-servers" not in _load_written("prod")


@respx.mock
def test_from_host_skips_server_with_unsupported_auth(caplog):
    _mock_discovery(
        "localhost",
        [_server("keep", 8010), _server("saml-app", 8011, auth="saml")],
    )

    tester = _get_tester()
    with caplog.at_level("WARNING"):
        tester.execute("prod --from-host=localhost --username=admin --password=pw")

    identifiers = [server["id"] for server in _load_written("prod")["app-servers"]]
    assert identifiers == ["keep"]
    assert "saml-app" in caplog.text
    assert "saml" in caplog.text.lower()


# --- host: auth mapping ------------------------------------------------------


@pytest.mark.parametrize(
    ("server_auth", "expected"),
    [
        ("basic", "basic"),
        ("digestbasic", "digestbasic"),
        ("certificate", "certificate"),
        ("kerberos-ticket", "kerberos"),
        ("application-level", "app"),
        ("oauth", "oauth"),
    ],
)
@respx.mock
def test_from_host_maps_discovered_server_auth(server_auth, expected):
    _mock_discovery("localhost", [_server("content", 8010, auth=server_auth)])

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    assert _load_written("prod")["app-servers"][0]["auth"] == expected


@pytest.mark.parametrize("server_auth", ["digest", "unknown-scheme", None])
@respx.mock
def test_from_host_treats_unmapped_server_auth_as_digest(server_auth):
    _mock_discovery("localhost", [_server("content", 8010, auth=server_auth)])

    tester = _get_tester()
    tester.execute("prod --from-host=localhost --username=admin --password=pw")

    assert "auth" not in _load_written("prod")["app-servers"][0]
