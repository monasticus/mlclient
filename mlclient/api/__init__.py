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

from .admin_api import AdminApi
from .databases import DatabasesApi
from .documents import DocumentsApi
from .eval import EvalApi
from .forests import ForestsApi
from .logs import LogsApi
from .manage_api import ManageApi
from .rest_api import RestApi
from .roles import RolesApi
from .servers import ServersApi
from .users import UsersApi

__all__ = [
    "AdminApi",
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
