import json
import re
from typing import Union

from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class DatabasePropertiesGetCall(ResourceCall):
    """
    A ResourceCall implementation representing a single GET request
    to the /manage/v2/databases/{id|name}/properties REST Resource

    This resource address returns the modifiable properties of the named database.
    The database can be identified either by ID or name.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/GET/manage/v2/databases/[id-or-name]/properties

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/databases/{}/properties"

    __FORMAT_PARAM = "format"

    __SUPPORTED_FORMATS = ["xml", "json", "html"]

    def __init__(self, database: str, data_format: str = "xml"):
        """
        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.
        """

        data_format = data_format if data_format is not None else "xml"
        DatabasePropertiesGetCall.__validate_params(data_format)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        self.__database = database
        self.add_param(DatabasePropertiesGetCall.__FORMAT_PARAM, data_format)

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Database Properties call

        Returns
        -------
        str
            an Database Properties call endpoint
        """

        return DatabasePropertiesGetCall.__ENDPOINT_TEMPLATE.format(self.__database)

    @staticmethod
    def __validate_params(data_format: str):
        if data_format not in DatabasePropertiesGetCall.__SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(DatabasePropertiesGetCall.__SUPPORTED_FORMATS)
            raise exceptions.WrongParameters("The supported formats are: " + joined_supported_formats)


class DatabasePropertiesPutCall(ResourceCall):
    """
    A ResourceCall implementation representing a single PUT request
    to the /manage/v2/databases/{id|name}/properties REST Resource

    This resource address modifies the properties of the named database.
    The list of modifiable properties can be returned by the GET version of this endpoint.
    The database can be identified either by id or name.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/PUT/manage/v2/databases/[id-or-name]/properties

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/databases/{}/properties"

    def __init__(self, database: str, body: Union[str, dict]):
        """
        Parameters
        ----------
        database : str
            A database identifier. The database can be identified either by ID or name.
        body : Union[str, dict]
            A database properties in XML or JSON format.
        """
        DatabasePropertiesPutCall.__validate_params(body)
        content_type = utils.get_content_type_header_for_data(body)
        body = body if content_type != constants.HEADER_JSON or not isinstance(body, str) else json.loads(body)
        super().__init__(method="PUT",
                         content_type=content_type,
                         body=body)
        self.__database = database

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Database Properties call

        Returns
        -------
        str
            an Database Properties call endpoint
        """

        return DatabasePropertiesPutCall.__ENDPOINT_TEMPLATE.format(self.__database)

    @staticmethod
    def __validate_params(body: Union[str, dict]):
        if body is None or isinstance(body, str) and re.search("^\\s*$", body):
            raise exceptions.WrongParameters("No request body provided for "
                                             "PUT /manage/v2/databases/{id|name}/properties!")
