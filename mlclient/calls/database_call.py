import json
import re
from typing import Union

from mlclient import constants, exceptions, utils
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

    def __init__(self, database: str, data_format: str = "xml", view: str = "default"):
        """
        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This parameter is not meaningful with view=edit.
        view : str
            A specific view of the returned data.
            Can be properties-schema, package, describe, config, counts, edit, status, forest-storage, or default.
        """

        data_format = data_format if data_format is not None else "xml"
        view = view if view is not None else "default"
        DatabaseGetCall.__validate_params(data_format, view)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        self.__database = database
        self.add_param(DatabaseGetCall.__FORMAT_PARAM, data_format)
        self.add_param(DatabaseGetCall.__VIEW_PARAM, view)

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Database call

        Returns
        -------
        str
            an Database call endpoint
        """

        return DatabaseGetCall.__ENDPOINT_TEMPLATE.format(self.__database)

    @staticmethod
    def __validate_params(data_format: str, view: str):
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

    def __init__(self, database: str, body: Union[str, dict]):
        """
        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        body : Union[str, dict]
            A database properties in XML or JSON format.
        """
        DatabasePostCall.__validate_params(body)
        content_type = utils.get_content_type_header_for_data(body)
        body = body if content_type != constants.HEADER_JSON or not isinstance(body, str) else json.loads(body)
        super().__init__(method="POST",
                         content_type=content_type,
                         body=body)
        self.__database = database

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Database call

        Returns
        -------
        str
            an Database call endpoint
        """

        return DatabasePostCall.__ENDPOINT_TEMPLATE.format(self.__database)

    @staticmethod
    def __validate_params(body: Union[str, dict]):
        if body is None or isinstance(body, str) and re.search("^\\s*$", body):
            raise exceptions.WrongParameters("No request body provided for POST /manage/v2/databases/{id|name}!")


class DatabaseDeleteCall(ResourceCall):
    """
    A ResourceCall implementation representing a single DELETE request
    to the /manage/v2/databases/{id|name} REST Resource

    This resource address deletes the named database from the cluster.
    The database can be identified either by id or name.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/DELETE/manage/v2/databases/[id-or-name]

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/databases/{}"

    __FOREST_DELETE_PARAM = "forest-delete"

    __SUPPORTED_FOREST_DELETE_OPTS = ["configuration", "data"]

    def __init__(self, database: str, forest_delete: str = None):
        """
        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        forest_delete : str
            Specifies to delete the forests attached to the database.
            If unspecified, the forests will not be affected.
            If "configuration" is specified, the forest configuration will be removed
            but public forest data will remain.
            If "data" is specified, the forest configuration and data will be removed.
        """
        DatabaseDeleteCall.__validate_params(forest_delete)
        super().__init__(method="DELETE")
        self.add_param(DatabaseDeleteCall.__FOREST_DELETE_PARAM, forest_delete)
        self.__database = database

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Database call

        Returns
        -------
        str
            an Database call endpoint
        """

        return DatabaseDeleteCall.__ENDPOINT_TEMPLATE.format(self.__database)

    @staticmethod
    def __validate_params(forest_delete: str):
        if forest_delete and forest_delete not in DatabaseDeleteCall.__SUPPORTED_FOREST_DELETE_OPTS:
            joined_supported_opts = ", ".join(DatabaseDeleteCall.__SUPPORTED_FOREST_DELETE_OPTS)
            raise exceptions.WrongParameters("The supported forest_delete options are: " + joined_supported_opts)
