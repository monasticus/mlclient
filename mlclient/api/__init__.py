"""Synchronous and asynchronous wrappers for MarkLogic REST endpoints."""

from mlclient.api.admin import AdminApi, AsyncAdminApi
from mlclient.api.databases import AsyncDatabasesApi, DatabasesApi
from mlclient.api.documents import AsyncDocumentsApi, DocumentsApi
from mlclient.api.eval import AsyncEvalApi, EvalApi
from mlclient.api.forests import AsyncForestsApi, ForestsApi
from mlclient.api.groups import AsyncGroupsApi, GroupsApi
from mlclient.api.hosts import AsyncHostsApi, HostsApi
from mlclient.api.logs import AsyncLogsApi, LogsApi
from mlclient.api.manage import AsyncManageApi, ManageApi
from mlclient.api.rest import AsyncRestApi, RestApi
from mlclient.api.roles import AsyncRolesApi, RolesApi
from mlclient.api.search import AsyncSearchApi, SearchApi
from mlclient.api.servers import AsyncServersApi, ServersApi
from mlclient.api.transactions import AsyncTransactionsApi, TransactionsApi
from mlclient.api.users import AsyncUsersApi, UsersApi
from mlclient.api.values import AsyncValuesApi, ValuesApi

__all__ = [
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
    "LogsApi",
    "ManageApi",
    "RestApi",
    "RolesApi",
    "SearchApi",
    "ServersApi",
    "TransactionsApi",
    "UsersApi",
    "ValuesApi",
]
