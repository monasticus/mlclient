import json
import re
from typing import Union

from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class ServerPropertiesGetCall(ResourceCall):
    """
    A ResourceCall implementation representing a single GET request
    to the /manage/v2/servers/{id|name}/properties REST Resource

    This resource address returns the current state of modifiable properties of the specified App Server.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/GET/manage/v2/servers/[id-or-name]/properties

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/servers/{}/properties"

    __GROUP_ID_PARAM = "group-id"
    __FORMAT_PARAM = "format"

    __SUPPORTED_FORMATS = ["xml", "json", "html"]

    def __init__(self, server: str, group_id: str, data_format: str = "xml"):
        """
        Parameters
        ----------
        server : str
            A server identifier. The server can be identified either by ID or name.
        group_id : str
            The id or name of the group to which the App Server belongs. This parameter is required.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.
        """

        data_format = data_format if data_format is not None else "xml"
        ServerPropertiesGetCall.__validate_params(data_format)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        self.__server = server
        self.add_param(ServerPropertiesGetCall.__GROUP_ID_PARAM, group_id)
        self.add_param(ServerPropertiesGetCall.__FORMAT_PARAM, data_format)

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Server Properties call

        Returns
        -------
        str
            a Server Properties call endpoint
        """

        return ServerPropertiesGetCall.__ENDPOINT_TEMPLATE.format(self.__server)

    @staticmethod
    def __validate_params(data_format: str):
        if data_format not in ServerPropertiesGetCall.__SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(ServerPropertiesGetCall.__SUPPORTED_FORMATS)
            raise exceptions.WrongParameters("The supported formats are: " + joined_supported_formats)


class ServerPropertiesPutCall(ResourceCall):
    """
    A ResourceCall implementation representing a single PUT request
    to the /manage/v2/servers/{id|name}/properties REST Resource

    Initiate a properties change on the specified App Server.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/PUT/manage/v2/servers/[id-or-name]/properties

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/servers/{}/properties"

    __GROUP_ID_PARAM = "group-id"

    def __init__(self, server: str, group_id: str, body: Union[str, dict]):
        """
        Parameters
        ----------
        server : str
            A server identifier. The server can be identified either by ID or name.
        group_id : str
            The id or name of the group to which the App Server belongs. This parameter is required.
        body : Union[str, dict]
            A database properties in XML or JSON format.
        """
        ServerPropertiesPutCall.__validate_params(body)
        content_type = utils.get_content_type_header_for_data(body)
        body = body if content_type != constants.HEADER_JSON or not isinstance(body, str) else json.loads(body)
        super().__init__(method="PUT",
                         content_type=content_type,
                         body=body)
        self.__server = server
        self.add_param(ServerPropertiesPutCall.__GROUP_ID_PARAM, group_id)

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Server Properties call

        Returns
        -------
        str
            a Server Properties call endpoint
        """

        return ServerPropertiesPutCall.__ENDPOINT_TEMPLATE.format(self.__server)

    @staticmethod
    def __validate_params(body: Union[str, dict]):
        if body is None or isinstance(body, str) and re.search("^\\s*$", body):
            raise exceptions.WrongParameters("No request body provided for "
                                             "PUT /manage/v2/servers/{id|name}/properties!")
