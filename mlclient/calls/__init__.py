"""The ML Calls package.

It contains modules dealing with MarkLogic REST Resources at the lowest level
of HTTP requests:

    * resource_call
        An abstract class representing a single request to a MarkLogic REST Resource.
    * database_call
        The ML Database Resource Calls module.
    * database_properties_call
        The ML Database Properties Resource Calls module.
    * databases_call
        The ML Databases Resource Calls module.
    * documents_call
        The ML Documents Resource Calls module.
    * eval_call
        The ML Eval Resource Call module.
    * forest_call
        The ML Forest Resource Calls module.
    * forest_properties_call
        The ML Forest Properties Resource Calls module.
    * forests_call
        The ML Forests Resource Calls module.
    * logs_call
        The ML Logs Resource Call module.
    * role_call
        The ML Role Resource Calls module.
    * role_properties_call
        The ML Role Properties Resource Calls module.
    * roles_call
        The ML Roles Resource Calls module.
    * server_call
        The ML Server Resource Calls module.
    * server_properties_call
        The ML Server Properties Resource Calls module.
    * servers_call
        The ML Servers Resource Calls module.
    * user_call
        The ML User Resource Calls module.
    * user_properties_call
        The ML User Properties Resource Calls module.
    * users_call
        The ML Users Resource Calls module.

This package exports the following classes:
    * ResourceCall
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
from .resource_call import ResourceCall
from .database_call import (DatabaseDeleteCall, DatabaseGetCall,
                            DatabasePostCall)
from .database_properties_call import (DatabasePropertiesGetCall,
                                       DatabasePropertiesPutCall)
from .databases_call import DatabasesGetCall, DatabasesPostCall
from .documents_call import DocumentsGetCall
from .eval_call import EvalCall
from .forest_call import (ForestDeleteCall, ForestGetCall,
                          ForestPostCall)
from .forest_properties_call import (ForestPropertiesGetCall,
                                     ForestPropertiesPutCall)
from .forests_call import (ForestsGetCall, ForestsPostCall,
                           ForestsPutCall)
from .logs_call import LogsCall
from .role_call import RoleDeleteCall, RoleGetCall
from .role_properties_call import (RolePropertiesGetCall,
                                   RolePropertiesPutCall)
from .roles_call import RolesGetCall, RolesPostCall
from .user_call import UserDeleteCall, UserGetCall
from .user_properties_call import (UserPropertiesGetCall,
                                   UserPropertiesPutCall)
from .users_call import UsersGetCall, UsersPostCall
from .server_call import ServerDeleteCall, ServerGetCall
from .server_properties_call import (ServerPropertiesGetCall,
                                     ServerPropertiesPutCall)
from .servers_call import ServersGetCall, ServersPostCall

__all__ = ["ResourceCall",
           "DatabaseDeleteCall", "DatabaseGetCall", "DatabasePostCall",
           "DatabasePropertiesGetCall", "DatabasePropertiesPutCall",
           "DatabasesGetCall", "DatabasesPostCall",
           "DocumentsGetCall",
           "EvalCall",
           "ForestDeleteCall", "ForestGetCall", "ForestPostCall",
           "ForestPropertiesGetCall", "ForestPropertiesPutCall",
           "ForestsGetCall", "ForestsPostCall", "ForestsPutCall",
           "LogsCall",
           "RoleDeleteCall", "RoleGetCall",
           "RolePropertiesGetCall", "RolePropertiesPutCall",
           "RolesGetCall", "RolesPostCall",
           "UserDeleteCall", "UserGetCall",
           "UserPropertiesGetCall", "UserPropertiesPutCall",
           "UsersGetCall", "UsersPostCall",
           "ServerDeleteCall", "ServerGetCall",
           "ServerPropertiesGetCall", "ServerPropertiesPutCall",
           "ServersGetCall", "ServersPostCall"]
