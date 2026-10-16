"""Protect canonical imports and the direction of implementation dependencies."""

import ast
import importlib
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3] / "mlclient"


def test_module_entrypoint_works_outside_checkout(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "mlclient", "--help"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Usage:" in result.stdout


EXPECTED_EXPORTS = {
    "mlclient.search.sq": [
        "and_",
        "and_not",
        "attribute",
        "boost",
        "box",
        "circle",
        "collection",
        "collection_constraint",
        "container",
        "container_constraint",
        "custom_constraint",
        "directory",
        "document",
        "document_fragment",
        "element",
        "element_constraint",
        "false",
        "field",
        "geo_attribute_pair",
        "geo_element",
        "geo_element_pair",
        "geo_json_property",
        "geo_json_property_pair",
        "geo_path",
        "geo_region_constraint",
        "geo_region_path",
        "geospatial_constraint",
        "json_property",
        "locks_fragment",
        "lsqt",
        "near",
        "not_",
        "not_in",
        "operator_state",
        "or_",
        "path_index",
        "period",
        "period_compare",
        "period_range",
        "point",
        "polygon",
        "properties_constraint",
        "properties_fragment",
        "qtext",
        "query",
        "range_",
        "range_constraint",
        "term",
        "true",
        "value",
        "value_constraint",
        "word",
        "word_constraint",
    ],
    "mlclient.search.opt": [
        "additional_query",
        "aggregate",
        "anchor",
        "annotation",
        "bucket",
        "callback",
        "collection",
        "collection_constraint",
        "computed_bucket",
        "concurrency_level",
        "constraint_value",
        "container_constraint",
        "control",
        "custom_constraint",
        "debug",
        "default_suggestion_source",
        "element_query_constraint",
        "extract_document_data",
        "extract_metadata",
        "forest",
        "fragment_scope",
        "geo_attribute_pair",
        "geo_constraint",
        "geo_element",
        "geo_element_pair",
        "geo_json_property",
        "geo_json_property_pair",
        "geo_path",
        "geo_region_path",
        "grammar",
        "heatmap",
        "implicit",
        "joiner",
        "metadata_qname",
        "native",
        "native_option",
        "operator",
        "operator_state",
        "options",
        "page_length",
        "preferred_matches",
        "properties_constraint",
        "quality_weight",
        "range_",
        "range_constraint",
        "result_decorator",
        "return_aggregates",
        "return_constraints",
        "return_facets",
        "return_frequencies",
        "return_metrics",
        "return_plan",
        "return_qtext",
        "return_query",
        "return_results",
        "return_similar",
        "return_values",
        "search_option",
        "searchable_expression",
        "sort",
        "starter",
        "suggestion_source",
        "term",
        "term_default",
        "transform_results",
        "tuples",
        "value",
        "value_constraint",
        "values",
        "word",
        "word_constraint",
        "word_lexicon",
    ],
    "mlclient.search.options": [
        "AdditionalQuery",
        "Aggregate",
        "Anchor",
        "Annotation",
        "Bucket",
        "Callback",
        "Collection",
        "CollectionConstraint",
        "ComputedBucket",
        "ConcurrencyLevel",
        "ConstraintValue",
        "ContainerConstraint",
        "Control",
        "CustomConstraint",
        "Debug",
        "DefaultSuggestionSource",
        "ElementQueryConstraint",
        "ExtractDocumentData",
        "ExtractMetadata",
        "Forest",
        "FragmentScope",
        "GeoAttributePair",
        "GeoConstraint",
        "GeoElement",
        "GeoElementPair",
        "GeoJsonProperty",
        "GeoJsonPropertyPair",
        "GeoPath",
        "GeoRegionPath",
        "Grammar",
        "Heatmap",
        "Implicit",
        "Joiner",
        "MetadataQName",
        "NativeOption",
        "NativeOptions",
        "Operator",
        "OperatorState",
        "PageLength",
        "PreferredMatches",
        "PropertiesConstraint",
        "QualityWeight",
        "Range",
        "RangeConstraint",
        "ResultDecorator",
        "ReturnAggregates",
        "ReturnConstraints",
        "ReturnFacets",
        "ReturnFrequencies",
        "ReturnMetrics",
        "ReturnPlan",
        "ReturnQtext",
        "ReturnQuery",
        "ReturnResults",
        "ReturnSimilar",
        "ReturnValues",
        "SearchOption",
        "SearchOptionString",
        "SearchOptions",
        "SearchableExpression",
        "SortOrder",
        "Starter",
        "SuggestionSource",
        "Term",
        "TermDefault",
        "TransformResults",
        "Tuples",
        "Value",
        "ValueConstraint",
        "Values",
        "Word",
        "WordConstraint",
        "WordLexicon",
    ],
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
        "DEFAULT_HEALTH_TIMEOUT",
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
    "mlclient.logging": ["MLLogHandler", "setup_logger", "setup_ml_logger"],
    "mlclient.models": [
        "SearchHit",
        "SearchReport",
        "TupleHit",
        "ValueHit",
        "BinaryDocument",
        "Document",
        "DocumentType",
        "JSONDocument",
        "MarkLogicVersion",
        "Metadata",
        "MetadataDocument",
        "Mimetype",
        "Permission",
        "ParsedValue",
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
        "AsyncInvokeApi",
        "AsyncLogsApi",
        "AsyncManageApi",
        "AsyncRestApi",
        "AsyncRolesApi",
        "AsyncSearchApi",
        "AsyncServersApi",
        "AsyncTransactionsApi",
        "AsyncUsersApi",
        "AsyncValuesApi",
        "DatabasesApi",
        "DocumentsApi",
        "EvalApi",
        "ForestsApi",
        "GroupsApi",
        "HostsApi",
        "InvokeApi",
        "LogsApi",
        "ManageApi",
        "RestApi",
        "RolesApi",
        "SearchApi",
        "ServersApi",
        "TransactionsApi",
        "UsersApi",
        "ValuesApi",
    ],
    "mlclient.calls": [
        "ApiCall",
        "ClusterConfigPostCall",
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
        "GroupDeleteCall",
        "GroupGetCall",
        "GroupPostCall",
        "GroupPropertiesGetCall",
        "GroupPropertiesPutCall",
        "GroupsGetCall",
        "GroupsPostCall",
        "HostConfigDeleteCall",
        "HostGetCall",
        "HostPostCall",
        "HostPropertiesGetCall",
        "HostPropertiesPutCall",
        "HostsGetCall",
        "InitPostCall",
        "InstanceAdminPostCall",
        "InvokeCall",
        "LogsCall",
        "RoleDeleteCall",
        "RoleGetCall",
        "RolePropertiesGetCall",
        "RolePropertiesPutCall",
        "RolesGetCall",
        "RolesPostCall",
        "SearchDeleteCall",
        "SearchGetCall",
        "SearchPostCall",
        "ServerConfigGetCall",
        "ServerDeleteCall",
        "ServerGetCall",
        "ServerPropertiesGetCall",
        "ServerPropertiesPutCall",
        "ServersGetCall",
        "ServersPostCall",
        "TimestampGetCall",
        "TimestampHeadCall",
        "TransactionGetCall",
        "TransactionPostCall",
        "TransactionsPostCall",
        "UserDeleteCall",
        "UserGetCall",
        "UserPropertiesGetCall",
        "UserPropertiesPutCall",
        "UsersGetCall",
        "UsersPostCall",
        "ValueGetCall",
        "ValuePostCall",
        "ValuesGetCall",
    ],
    "mlclient.services": [
        "AsyncCtsService",
        "AsyncDocumentsService",
        "AsyncEvalService",
        "AsyncInvokeService",
        "AsyncSearchService",
        "AsyncTransactionService",
        "CtsService",
        "DocumentsService",
        "EvalService",
        "InvokeService",
        "SearchScope",
        "ServiceScope",
        "SearchService",
        "TransactionService",
        "async_open_transaction",
        "open_transaction",
    ],
    "mlclient.services.diagnostics": [
        "AsyncLogsService",
        "LogLevelService",
        "LogsService",
        "TraceEvents",
        "TraceEventsService",
    ],
    "mlclient.search": [
        "opt",
        "sq",
        "QueryComponent",
        "SearchQuery",
    ],
    "mlclient.search.structured": [
        "AndNotQuery",
        "AndQuery",
        "Attribute",
        "BoostQuery",
        "Box",
        "Circle",
        "CollectionConstraintQuery",
        "CollectionQuery",
        "ContainerConstraintQuery",
        "ContainerQuery",
        "CustomConstraintQuery",
        "DirectoryQuery",
        "DocumentFragmentQuery",
        "DocumentQuery",
        "Element",
        "ElementConstraintQuery",
        "FalseQuery",
        "Field",
        "GeoAttributePairQuery",
        "GeoElementPairQuery",
        "GeoElementQuery",
        "GeoJsonPropertyPairQuery",
        "GeoJsonPropertyQuery",
        "GeoPathQuery",
        "GeoRegionConstraintQuery",
        "GeoRegionPathQuery",
        "GeospatialConstraintQuery",
        "JsonProperty",
        "LocksFragmentQuery",
        "LsqtQuery",
        "NearQuery",
        "NotInQuery",
        "NotQuery",
        "OperatorState",
        "OrQuery",
        "PathIndex",
        "Period",
        "PeriodCompareQuery",
        "PeriodRangeQuery",
        "Point",
        "Polygon",
        "PropertiesConstraintQuery",
        "PropertiesFragmentQuery",
        "QtextQuery",
        "Query",
        "QueryTarget",
        "RangeConstraintQuery",
        "RangeQuery",
        "Region",
        "SEARCH_NS_URI",
        "StructuredQuery",
        "TermQuery",
        "TrueQuery",
        "ValueConstraintQuery",
        "ValueQuery",
        "WordConstraintQuery",
        "WordQuery",
    ],
    "mlclient.xquery": [
        "LOCAL_NS_URI",
        "AtomicValue",
        "Cts",
        "DatabaseRoot",
        "Fn",
        "FunctionCall",
        "Index",
        "ModuleFunctionCall",
        "NodeInput",
        "PythonNode",
        "NamespaceMap",
        "Path",
        "Range",
        "ResultXPath",
        "Xdmp",
        "XqyCompilationContext",
        "XqyExpression",
        "XqySequence",
        "Xs",
        "as_searchable_expression",
        "cts",
        "fn",
        "namespace_bindings",
        "xdmp",
        "xpath",
        "xs",
        "CTS_NS_URI",
        "CtsQuery",
        "AfterQuery",
        "AndNotQuery",
        "AndQuery",
        "BeforeQuery",
        "BoostQuery",
        "Box",
        "Circle",
        "CollectionQuery",
        "ColumnRangeQuery",
        "DirectoryQuery",
        "DocumentFormatQuery",
        "DocumentFragmentQuery",
        "DocumentPermissionQuery",
        "DocumentQuery",
        "DocumentRootQuery",
        "ElementAttributePairGeospatialQuery",
        "ElementAttributeRangeQuery",
        "ElementAttributeValueQuery",
        "ElementAttributeWordQuery",
        "ElementChildGeospatialQuery",
        "ElementGeospatialQuery",
        "ElementPairGeospatialQuery",
        "ElementQuery",
        "ElementRangeQuery",
        "ElementValueQuery",
        "ElementWordQuery",
        "FalseQuery",
        "FieldRangeQuery",
        "FieldValueQuery",
        "FieldWordQuery",
        "GeospatialRegionQuery",
        "JsonPropertyChildGeospatialQuery",
        "JsonPropertyGeospatialQuery",
        "JsonPropertyPairGeospatialQuery",
        "JsonPropertyRangeQuery",
        "JsonPropertyScopeQuery",
        "JsonPropertyValueQuery",
        "JsonPropertyWordQuery",
        "LocksFragmentQuery",
        "LsqtQuery",
        "NearQuery",
        "NotInQuery",
        "NotQuery",
        "OrQuery",
        "PathGeospatialQuery",
        "PathRangeQuery",
        "Period",
        "PeriodCompareQuery",
        "PeriodRangeQuery",
        "Point",
        "Polygon",
        "PropertiesFragmentQuery",
        "RangeQuery",
        "RegisteredQuery",
        "ReverseQuery",
        "RuntimeQuery",
        "SimilarQuery",
        "TripleRangeQuery",
        "TrueQuery",
        "WordQuery",
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


def _mlclient_imports(path: Path) -> set[str]:
    """Return the mlclient modules imported by every Python file under a path."""
    paths = path.rglob("*.py") if path.is_dir() else [path]
    return {
        module
        for source in paths
        for module in _imported_modules(source)
        if module.startswith("mlclient")
    }


def _imported_modules(source: Path) -> set[str]:
    """Return the absolute names of the modules a Python file imports."""
    modules = set()
    for node in ast.walk(ast.parse(source.read_text())):
        if isinstance(node, ast.ImportFrom):
            modules.add(_absolute_module(source, node))
        elif isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
    return modules


def _absolute_module(source: Path, node: ast.ImportFrom) -> str:
    """Resolve an import-from statement, relative or not, to a module name."""
    if not node.level:
        return node.module
    package = source.relative_to(ROOT.parent).with_suffix("").parts[: -node.level]
    return ".".join([*package, node.module] if node.module else package)


def test_search_package_does_not_depend_on_xquery():
    root = ROOT / "search"
    imports = _mlclient_imports(root)
    assert not {module for module in imports if module.startswith("mlclient.xquery")}


def test_compiler_and_cts_queries_do_not_depend_on_function_builders():
    root = ROOT / "xquery"
    for name in ("expressions.py", "_cts_query.py"):
        imports = _mlclient_imports(root / name)
        allowed = {"mlclient.xquery.expressions", "mlclient.search.base"}
        if name == "_cts_query.py":
            # The combined-query options parameter names this public input type.
            allowed.add("mlclient.search.options")
        assert imports <= allowed, name


@pytest.mark.parametrize(
    "module",
    [
        "mlclient.search",
        "mlclient.search.structured",
        "mlclient.search.options",
        "mlclient.xquery",
        "mlclient.xquery.expressions",
    ],
)
def test_every_query_module_imports_first_in_a_fresh_interpreter(module):
    subprocess.run([sys.executable, "-c", f"import {module}"], check=True)


def test_services_use_only_public_xquery_imports():
    for source in (ROOT / "services").rglob("*.py"):
        for node in ast.walk(ast.parse(source.read_text())):
            if isinstance(node, ast.ImportFrom):
                modules = [_absolute_module(source, node)]
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.Import):
                modules = names = [alias.name for alias in node.names]
            else:
                continue
            for module in modules:
                if module.startswith("mlclient.xquery"):
                    parts = module.split(".")
                    assert not any(part.startswith("_") for part in parts), source
                    assert not any(name.startswith("_") for name in names), source


def test_low_level_modules_do_not_depend_on_composition():
    root = ROOT
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
        "search",
        "xquery",
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
