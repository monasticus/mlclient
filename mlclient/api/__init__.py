"""Synchronous and asynchronous wrappers for MarkLogic REST endpoints."""

from mlclient.api.admin import AdminApi, AsyncAdminApi
from mlclient.api.databases import AsyncDatabasesApi, DatabasesApi
from mlclient.api.documents import AsyncDocumentsApi, DocumentsApi
from mlclient.api.eval import AsyncEvalApi, EvalApi
from mlclient.api.forests import AsyncForestsApi, ForestsApi
from mlclient.api.groups import AsyncGroupsApi, GroupsApi
from mlclient.api.logs import AsyncLogsApi, LogsApi
from mlclient.api.manage import AsyncManageApi, ManageApi
from mlclient.api.rest import AsyncRestApi, RestApi
from mlclient.api.roles import AsyncRolesApi, RolesApi
from mlclient.api.servers import AsyncServersApi, ServersApi
from mlclient.api.transactions import AsyncTransactionsApi, TransactionsApi
from mlclient.api.users import AsyncUsersApi, UsersApi

__all__ = [
    "AdminApi",
    "AsyncAdminApi",
    "AsyncDatabasesApi",
    "AsyncDocumentsApi",
    "AsyncEvalApi",
    "AsyncForestsApi",
    "AsyncGroupsApi",
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
    "LogsApi",
    "ManageApi",
    "RestApi",
    "RolesApi",
    "ServersApi",
    "TransactionsApi",
    "UsersApi",
]
