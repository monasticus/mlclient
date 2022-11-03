import json
import re
from typing import Union

from mlclient import exceptions, utils, constants
from mlclient.calls import ResourceCall


class DatabaseGetCall(ResourceCall):
    """
    A ResourceCall implementation representing a single GET request to the /manage/v2/databases/{id|name} REST Resource

    This resource address returns information on the specified database.
    The database can be identified either by ID or name.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/databases/[id-or-name]

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/databases/{}"

    __FORMAT_PARAM = "format"
    __VIEW_PARAM = "view"

    __SUPPORTED_FORMATS = ["xml", "json", "html"]
    __SUPPORTED_VIEWS = ["describe", "default", "config", "counts", "edit",
                         "package", "status", "forest-storage", "properties-schema"]

    def __init__(self, database_id: str = None, database_name: str = None,
                 data_format: str = "xml", view: str = "default"):
        """
        Parameters
        ----------
        database_id : str
            A database ID. You must include either this parameter or the database_name parameter.
            When included both, the database_name is ignored.
        database_name : str
            A database name. You must include either this parameter or the database_id parameter.
            When included both, the database_name is ignored.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This parameter is not meaningful with view=edit.
        view : str
            A specific view of the returned data.
            Can be properties-schema, package, describe, config, counts, edit, status, forest-storage, or default.
        """

        data_format = data_format if data_format is not None else "xml"
        view = view if view is not None else "default"
        DatabaseGetCall.__validate_params(database_id, database_name, data_format, view)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        self.__id = database_id
        self.__name = database_name
        self.add_param(DatabaseGetCall.__FORMAT_PARAM, data_format)
        self.add_param(DatabaseGetCall.__VIEW_PARAM, view)

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Database call

        Returns
        -------
        str
            an Database call endpoint
        """

        return DatabaseGetCall.__ENDPOINT_TEMPLATE.format(self.__id if self.__id else self.__name)

    @staticmethod
    def __validate_params(database_id: str, database_name: str, data_format: str, view: str):
        if not database_id and not database_name:
            raise exceptions.WrongParameters("You must include either the database_id or the database_name parameter!")
        if data_format not in DatabaseGetCall.__SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(DatabaseGetCall.__SUPPORTED_FORMATS)
            raise exceptions.WrongParameters("The supported formats are: " + joined_supported_formats)
        if view not in DatabaseGetCall.__SUPPORTED_VIEWS:
            joined_supported_views = ", ".join(DatabaseGetCall.__SUPPORTED_VIEWS)
            raise exceptions.WrongParameters("The supported views are: " + joined_supported_views)


class DatabasePostCall(ResourceCall):
    """
    A ResourceCall implementation representing a single POST request to the /manage/v2/databases/{id|name} REST Resource

    This resource address can be used to clear the contents of the named database
    and to perform various configuration operations on the database.
    The database can be identified either by id or name.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/manage/v2/databases/[id-or-name]

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/databases/{}"

    def __init__(self, database_id: str = None, database_name: str = None, body: Union[str, dict] = None):
        """
        Parameters
        ----------
        database_id : str
            A database ID. You must include either this parameter or the database_name parameter.
            When included both, the database_name is ignored.
        database_name : str
            A database name. You must include either this parameter or the database_id parameter.
            When included both, the database_name is ignored.
        body : Union[str, dict]
            A database properties in XML or JSON format.
        """
        DatabasePostCall.__validate_params(database_id, database_name, body)
        content_type = utils.get_content_type_header_for_data(body)
        body = body if content_type != constants.HEADER_JSON or not isinstance(body, str) else json.loads(body)
        super().__init__(method="POST",
                         content_type=content_type,
                         body=body)
        self.__id = database_id
        self.__name = database_name

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Database call

        Returns
        -------
        str
            an Database call endpoint
        """

        return DatabasePostCall.__ENDPOINT_TEMPLATE.format(self.__id if self.__id else self.__name)

    @staticmethod
    def __validate_params(database_id: str, database_name: str, body: Union[str, dict]):
        if not database_id and not database_name:
            raise exceptions.WrongParameters("You must include either the database_id or the database_name parameter!")
        if not body or body is None or isinstance(body, str) and re.search("^\\s*$", body):
            endpoint = DatabasePostCall.__ENDPOINT_TEMPLATE.format(database_id if database_id else database_name)
            raise exceptions.WrongParameters(f"No request body provided for POST {endpoint}!")
