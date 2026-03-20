"""The ML API package.

API endpoint groups providing mid-level access to MarkLogic resources.
Each API class wraps ApiCall objects and returns raw Response objects.
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
