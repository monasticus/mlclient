import json
from typing import Union

from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class DatabasesCall(ResourceCall):
    """
    A ResourceCall implementation representing a single request to the /manage/v2/databases REST Resource

    This resource address
    - (GET) returns a summary of the databases in the cluster.
    - (POST) creates a new database in the cluster.

    Documentation of the REST Resource API:
        - https://docs.marklogic.com/REST/GET/manage/v2/databases
        - https://docs.marklogic.com/REST/POST/manage/v2/databases

    Attributes
    ----------
    ENDPOINT
        a static constant storing the Databases endpoint value

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    ENDPOINT = "/manage/v2/databases"

    __FORMAT_PARAM = "format"
    __VIEW_PARAM = "view"

    __SUPPORTED_FORMATS = ["xml", "json", "html"]
    __SUPPORTED_VIEWS = ["describe", "default", "metrics", "package", "schema", "properties-schema"]

    def __init__(self, method: str, data_format: str = "xml", view: str = "default", body: Union[str, dict] = None):
        """
        Parameters
        ----------
        method : str
            A request method.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data. Can be schema, metrics, package, or default.
        body : Union[str, dict]
            A database properties in XML or JSON format.
        """

        data_format = data_format if data_format is not None else "xml"
        if data_format not in DatabasesCall.__SUPPORTED_FORMATS:
            raise exceptions.WrongParameters("The supported formats are: " + ", ".join(DatabasesCall.__SUPPORTED_FORMATS))

        super().__init__(method=method,
                         accept=utils.get_accept_header_for_format(data_format))
        if method == constants.METHOD_GET:
            self.__init_get(data_format, view)
        elif method == constants.METHOD_POST:
            self.__init_post(data_format, body)
        else:
            raise exceptions.WrongParameters("Method not allowed: the supported methods are GET and POST!")

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Databases call

        Returns
        -------
        str
            an Databases call endpoint
        """

        return DatabasesCall.ENDPOINT

    def __init_get(self, data_format: str, view: str):
        view = view if view is not None else "default"
        if view not in DatabasesCall.__SUPPORTED_VIEWS:
            raise exceptions.WrongParameters("The supported views are: " + ", ".join(DatabasesCall.__SUPPORTED_VIEWS))
        self.add_param(DatabasesCall.__VIEW_PARAM, view)
        self.add_param(DatabasesCall.__FORMAT_PARAM, data_format)

    def __init_post(self, data_format: str, body):
        if body is None:
            raise exceptions.WrongParameters("No request body provided for POST /manage/v2/databases!")

        content_type = utils.get_content_type_header_for_data(body)
        body = body if content_type != constants.HEADER_JSON or not isinstance(body, str) else json.loads(body)
        self.add_param(DatabasesCall.__FORMAT_PARAM, data_format)
        self.add_header(constants.HEADER_NAME_CONTENT_TYPE, content_type)
        self.set_body(body)
