"""Protect canonical imports and the direction of implementation dependencies."""

import ast
import importlib
import subprocess
import sys
from pathlib import Path

import pytest

EXPECTED_EXPORTS = {
    "mlclient": ["MLClient", "AsyncMLClient", "MLClientManager", "__version__"],
    "mlclient.clients": [
        "HttpClient",
        "AsyncHttpClient",
        "ApiClient",
        "AsyncApiClient",
    ],
    "mlclient.env": [
        "DEFAULT_APP_SERVER_SETTINGS",
        "MLEnvironment",
        "MLServerConfig",
        "find_mlclient_directory",
        "find_mlclient_environment",
    ],
    "mlclient.http": [
        "HTTPConfig",
        "DEFAULT_TIMEOUT",
        "DEFAULT_RETRY_STRATEGY",
        "NO_RETRY_STRATEGY",
        "UNSET",
    ],
    "mlclient.auth": [
        "AuthConfig",
        "AuthParam",
        "OAuthBearerAuth",
        "KerberosAuth",
        "MarkLogicCloudAuth",
    ],
    "mlclient.connection": [
        "SSLConfig",
        "CloudConfig",
        "MARKLOGIC_APP_SERVICES_PORT",
        "MARKLOGIC_ADMIN_PORT",
        "MARKLOGIC_MANAGE_PORT",
        "MARKLOGIC_HEALTHCHECK_PORT",
    ],
    "mlclient.responses": ["MLResponseParser"],
    "mlclient.multipart": [
        "MultipartPart",
        "encode_multipart_mixed",
        "decode_multipart_mixed",
    ],
    "mlclient.logging": ["setup_logger"],
    "mlclient.models": [
        "BinaryDocument",
        "Document",
        "DocumentType",
        "JSONDocument",
        "MarkLogicVersion",
        "Metadata",
        "MetadataDocument",
        "Mimetype",
        "Permission",
        "TextDocument",
        "XMLDocument",
        "Category",
        "DocumentsBodyPart",
        "DocumentsBodyPartType",
        "DocumentsDisposition",
        "Extract",
        "Repair",
        "LogType",
        "Mimetypes",
    ],
    "mlclient.api": [
        "AdminApi",
        "AsyncAdminApi",
        "AsyncDatabasesApi",
        "AsyncDocumentsApi",
        "AsyncEvalApi",
        "AsyncForestsApi",
        "AsyncGroupsApi",
        "AsyncHostsApi",
        "AsyncLogsApi",
        "AsyncManageApi",
        "AsyncRestApi",
        "AsyncRolesApi",
        "AsyncServersApi",
        "AsyncTransactionsApi",
        "AsyncUsersApi",
        "DatabasesApi",
        "DocumentsApi",
        "EvalApi",
        "ForestsApi",
        "GroupsApi",
        "HostsApi",
        "LogsApi",
        "ManageApi",
        "RestApi",
        "RolesApi",
        "ServersApi",
        "TransactionsApi",
        "UsersApi",
    ],
    "mlclient.calls": [
        "ApiCall",
        "DatabaseDeleteCall",
        "DatabaseGetCall",
        "DatabasePostCall",
        "DatabasePropertiesGetCall",
        "DatabasePropertiesPutCall",
        "DatabasesGetCall",
        "DatabasesPostCall",
        "DocumentsDeleteCall",
        "DocumentsGetCall",
        "DocumentsPostCall",
        "EvalCall",
        "ForestDeleteCall",
        "ForestGetCall",
        "ForestPostCall",
        "ForestPropertiesGetCall",
        "ForestPropertiesPutCall",
        "ForestsGetCall",
        "ForestsPostCall",
        "ForestsPutCall",
        "GroupPropertiesGetCall",
        "GroupPropertiesPutCall",
        "HostsGetCall",
        "LogsCall",
        "RoleDeleteCall",
        "RoleGetCall",
        "RolePropertiesGetCall",
        "RolePropertiesPutCall",
        "RolesGetCall",
        "RolesPostCall",
        "ServerConfigGetCall",
        "ServerDeleteCall",
        "ServerGetCall",
        "ServerPropertiesGetCall",
        "ServerPropertiesPutCall",
        "ServersGetCall",
        "ServersPostCall",
        "TimestampGetCall",
        "TransactionGetCall",
        "TransactionPostCall",
        "TransactionsPostCall",
        "UserDeleteCall",
        "UserGetCall",
        "UserPropertiesGetCall",
        "UserPropertiesPutCall",
        "UsersGetCall",
        "UsersPostCall",
    ],
    "mlclient.services": [
        "AsyncCtsService",
        "AsyncDocumentsService",
        "AsyncEvalService",
        "AsyncLogsService",
        "AsyncTransactionService",
        "CtsService",
        "DocumentsService",
        "EvalService",
        "LogLevelService",
        "LogsService",
        "TraceEvents",
        "TraceEventsService",
        "TransactionService",
        "async_open_transaction",
        "open_transaction",
    ],
    "mlclient.functions": [],
    "mlclient.functions.xqy": [
        "CompilationContext",
        "Cts",
        "Expression",
        "Fn",
        "Xdmp",
        "Xs",
        "cts",
        "fn",
        "namespace_bindings",
        "xdmp",
        "xpath",
        "xs",
    ],
    "mlclient.io": ["DocumentsLoader", "DocumentsWriter"],
    "mlclient.jobs": [
        "DocumentJobReport",
        "ReadDocumentsJob",
        "WriteDocumentsJob",
        "DocumentReport",
        "DocumentStatus",
        "DocumentStatusDetails",
    ],
    "mlclient.exceptions": [
        "WrongParametersError",
        "ConfigError",
        "UnsupportedFormatError",
        "MLClientDirectoryNotFoundError",
        "MLClientEnvironmentNotFoundError",
        "NoSuchAppServerError",
        "NotARestServerError",
        "NoRestServerConfiguredError",
        "InvalidLogTypeError",
        "MarkLogicError",
        "UnsupportedFileExtensionError",
        "InvalidMetadataError",
        "ResourceNotFoundError",
        "EnvironmentFileExistsError",
    ],
}


@pytest.mark.parametrize(("namespace", "names"), EXPECTED_EXPORTS.items())
def test_canonical_exports(namespace, names):
    module = importlib.import_module(namespace)
    assert set(module.__all__) == set(names)
    for name in names:
        assert getattr(module, name) is not None


def test_imports_in_a_fresh_interpreter():
    imports = "\n".join(
        f"from {namespace} import {', '.join(names)}"
        if names
        else f"import {namespace}"
        for namespace, names in reversed(EXPECTED_EXPORTS.items())
    )
    subprocess.run([sys.executable, "-c", imports], check=True)


def test_services_use_only_public_xquery_imports():
    root = Path(__file__).resolve().parents[3] / "mlclient" / "services"
    for source in root.glob("*.py"):
        for node in ast.walk(ast.parse(source.read_text())):
            if isinstance(node, ast.ImportFrom) and (node.module or "").startswith(
                "mlclient.functions",
            ):
                assert not any(part.startswith("_") for part in node.module.split("."))
                assert not any(alias.name.startswith("_") for alias in node.names)


def test_low_level_modules_do_not_depend_on_composition():
    root = Path(__file__).resolve().parents[3] / "mlclient"
    lower = [
        "auth.py",
        "connection.py",
        "http.py",
        "_utils.py",
        "_options.py",
        "_constants.py",
        "exceptions.py",
        "multipart.py",
        "models",
        "calls",
        "clients",
    ]
    forbidden = {"_client", "_manager", "env", "api", "services", "cli", "jobs"}
    for relative in lower:
        path = root / relative
        paths = path.rglob("*.py") if path.is_dir() else [path]
        for source in paths:
            for node in ast.walk(ast.parse(source.read_text())):
                if isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    if node.level:
                        package = ".".join(
                            ("mlclient", *source.relative_to(root).parts[:-1]),
                        )
                        module = importlib.util.resolve_name(
                            "." * node.level + module,
                            package,
                        )
                    if module == "mlclient":
                        names = [alias.name for alias in node.names]
                        assert not {
                            "MLClient",
                            "AsyncMLClient",
                            "MLClientManager",
                        } & set(names), source
                        assert not forbidden & set(names), source
                    elif module.startswith("mlclient."):
                        assert module.split(".")[1] not in forbidden, (
                            source,
                            node.module,
                        )
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("mlclient."):
                            assert alias.name.split(".")[1] not in forbidden, (
                                source,
                                alias.name,
                            )
