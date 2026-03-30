"""The ML API package.

It exports 3 top-level API group classes:
    * RestApi
        REST Client API (/v1/* endpoints).
    * ManageApi
        Management API (/manage/v2/* endpoints).
    * AdminApi
        Admin API (/admin/v1/* endpoints).

It also exports resource-level API classes used by RestApi and ManageApi:
    * DatabasesApi, DocumentsApi, EvalApi, ForestsApi, LogsApi,
      RolesApi, ServersApi, UsersApi

Each resource-level API wraps ApiCall objects and returns raw httpx.Response objects.
"""

from .admin_api import AdminApi, AsyncAdminApi
from .databases import AsyncDatabasesApi, DatabasesApi
from .documents import AsyncDocumentsApi, DocumentsApi
from .eval import AsyncEvalApi, EvalApi
from .forests import AsyncForestsApi, ForestsApi
from .logs import AsyncLogsApi, LogsApi
from .manage_api import AsyncManageApi, ManageApi
from .rest_api import AsyncRestApi, RestApi
from .roles import AsyncRolesApi, RolesApi
from .servers import AsyncServersApi, ServersApi
from .users import AsyncUsersApi, UsersApi

__all__ = [
    "AdminApi",
    "AsyncAdminApi",
    "AsyncDatabasesApi",
    "AsyncDocumentsApi",
    "AsyncEvalApi",
    "AsyncForestsApi",
    "AsyncLogsApi",
    "AsyncManageApi",
    "AsyncRestApi",
    "AsyncRolesApi",
    "AsyncServersApi",
    "AsyncUsersApi",
    "DatabasesApi",
    "DocumentsApi",
    "EvalApi",
    "ForestsApi",
    "LogsApi",
    "ManageApi",
    "RestApi",
    "RolesApi",
    "ServersApi",
    "UsersApi",
]
