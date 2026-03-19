"""The ML Calls package.

It contains modules dealing with MarkLogic REST Resources at the lowest level
of HTTP requests. Additionally, it exports the following package:

    * model
        The ML Calls Model package.

This package exports the following modules:

    * rest
        An abstract class representing a single request to a MarkLogic REST Resource.
    * databases
        The ML Database Resource Calls module.
    * documents
        The ML Documents Resource Calls module.
    * eval
        The ML Eval Resource Call module.
    * forests
        The ML Forest Resource Calls module.
    * logs
        The ML Logs Resource Call module.
    * roles
        The ML Role Resource Calls module.
    * servers
        The ML Server Resource Calls module.
    * users
        The ML User Resource Calls module.

This package exports the following classes:
    * RestCall
        An abstract class representing a single request to a MarkLogic REST Resource.
    * DatabaseGetCall
        A GET request to get database details.
    * DatabasePostCall
        A POST request to manage a database.
    * DatabaseDeleteCall
        A DELETE request to remove a database from a cluster.
    * DatabasePropertiesGetCall
        A GET request to get a database properties.
    * DatabasePropertiesPutCall
        A PUT request to modify database properties.
    * DatabasesGetCall
        A GET request to get databases summary.
    * DatabasesPostCall
        A POST request to create a new database.
    * DocumentsGetCall
        A GET request to retrieve documents' content or metadata.
    * DocumentsDeleteCall
        A DELETE request to remove documents, or reset document metadata.
    * DocumentsPostCall
        A POST request to insert or update documents' content or metadata.
    * EvalCall
        A POST request to evaluate an ad-hoc query.
    * ForestGetCall
        A GET request to get a forest details.
    * ForestPostCall
        A POST request to change a forest's state.
    * ForestDeleteCall
        A DELETE request to remove a forest.
    * ForestPropertiesGetCall
        A GET request to get forest properties.
    * ForestPropertiesPutCall
        A PUT request to modify forest properties.
    * ForestsGetCall
        A GET request to get forests summary.
    * ForestsPostCall
        A POST request to create a new forest.
    * ForestsPutCall
        A PUT request to perform an operation on forests.
    * LogsCall
        A GET request to retrieve logs.
    * RoleGetCall
        A GET request to get a role details.
    * RoleDeleteCall
        A DELETE request to remove a role.
    * RolePropertiesGetCall
        A GET request to get role properties.
    * RolePropertiesPutCall
        A PUT request to modify role properties.
    * RolesGetCall
        A GET request to get roles summary.
    * RolesPostCall
        A POST request to create a new role.
    * ServerGetCall
        A GET request to get app server details.
    * ServerDeleteCall
        A DELETE request to remove an app server.
    * ServerPropertiesGetCall
        A GET request to get app server properties.
    * ServerPropertiesPutCall
        A PUT request to modify app server properties.
    * ServersGetCall
        A GET request to get app servers summary.
    * ServersPostCall
        A POST request to create a new app server.
    * UserGetCall
        A GET request to get user details.
    * UserDeleteCall
        A DELETE request to remove a user.
    * UserPropertiesGetCall
        A GET request to get user properties.
    * UserPropertiesPutCall
        A PUT request to modify user properties.
    * UsersGetCall
        A GET request to get users summary.
    * UsersPostCall
        A POST request to create a new user.

Examples
--------
>>> from mlclient.calls import DatabaseGetCall, EvalCall
"""

from .rest import RestCall
from .databases import (
    DatabaseDeleteCall,
    DatabaseGetCall,
    DatabasePostCall,
    DatabasePropertiesGetCall,
    DatabasePropertiesPutCall,
    DatabasesGetCall,
    DatabasesPostCall,
)
from .documents import DocumentsDeleteCall, DocumentsGetCall, DocumentsPostCall
from .eval import EvalCall
from .forests import (
    ForestDeleteCall,
    ForestGetCall,
    ForestPostCall,
    ForestPropertiesGetCall,
    ForestPropertiesPutCall,
    ForestsGetCall,
    ForestsPostCall,
    ForestsPutCall,
)
from .logs import LogsCall
from .roles import (
    RoleDeleteCall,
    RoleGetCall,
    RolePropertiesGetCall,
    RolePropertiesPutCall,
    RolesGetCall,
    RolesPostCall,
)
from .servers import (
    ServerDeleteCall,
    ServerGetCall,
    ServerPropertiesGetCall,
    ServerPropertiesPutCall,
    ServersGetCall,
    ServersPostCall,
)
from .users import (
    UserDeleteCall,
    UserGetCall,
    UserPropertiesGetCall,
    UserPropertiesPutCall,
    UsersGetCall,
    UsersPostCall,
)

__all__ = [
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
    "LogsCall",
    "RestCall",
    "RoleDeleteCall",
    "RoleGetCall",
    "RolePropertiesGetCall",
    "RolePropertiesPutCall",
    "RolesGetCall",
    "RolesPostCall",
    "ServerDeleteCall",
    "ServerGetCall",
    "ServerPropertiesGetCall",
    "ServerPropertiesPutCall",
    "ServersGetCall",
    "ServersPostCall",
    "UserDeleteCall",
    "UserGetCall",
    "UserPropertiesGetCall",
    "UserPropertiesPutCall",
    "UsersGetCall",
    "UsersPostCall",
]
