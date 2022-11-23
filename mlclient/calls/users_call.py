import json
import re
from typing import Union

from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class UsersGetCall(ResourceCall):
    """
    A ResourceCall implementation representing a single GET request to the /manage/v2/users REST Resource

    This resource address returns a summary of the users in the cluster.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/users

    Attributes
    ----------
    ENDPOINT
        a static constant storing the Users endpoint value

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    ENDPOINT = "/manage/v2/users"

    __FORMAT_PARAM = "format"
    __VIEW_PARAM = "view"

    __SUPPORTED_FORMATS = ["xml", "json", "html"]
    __SUPPORTED_VIEWS = ["describe", "default"]

    def __init__(self, data_format: str = "xml", view: str = "default"):
        """
        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data. Can be: describe, or default.
        """

        data_format = data_format if data_format is not None else "xml"
        view = view if view is not None else "default"
        UsersGetCall.__validate_params(data_format, view)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        self.add_param(UsersGetCall.__FORMAT_PARAM, data_format)
        self.add_param(UsersGetCall.__VIEW_PARAM, view)

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Users call

        Returns
        -------
        str
            an Users call endpoint
        """

        return UsersGetCall.ENDPOINT

    @staticmethod
    def __validate_params(data_format: str, view: str):
        if data_format not in UsersGetCall.__SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(UsersGetCall.__SUPPORTED_FORMATS)
            raise exceptions.WrongParameters("The supported formats are: " + joined_supported_formats)
        if view not in UsersGetCall.__SUPPORTED_VIEWS:
            joined_supported_views = ", ".join(UsersGetCall.__SUPPORTED_VIEWS)
            raise exceptions.WrongParameters("The supported views are: " + joined_supported_views)


class UsersPostCall(ResourceCall):
    """
    A ResourceCall implementation representing a single POST request to the /manage/v2/users REST Resource

    This resource address creates a new user in the security database.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/manage/v2/users

    Attributes
    ----------
    ENDPOINT
        a static constant storing the Users endpoint value

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    ENDPOINT = "/manage/v2/users"

    def __init__(self, body: Union[str, dict]):
        """
        Parameters
        ----------
        body : Union[str, dict]
            A user properties in XML or JSON format.
        """
        UsersPostCall.__validate_params(body)
        content_type = utils.get_content_type_header_for_data(body)
        body = body if content_type != constants.HEADER_JSON or not isinstance(body, str) else json.loads(body)
        super().__init__(method="POST",
                         content_type=content_type,
                         body=body)

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Users call

        Returns
        -------
        str
            an Users call endpoint
        """

        return UsersPostCall.ENDPOINT

    @staticmethod
    def __validate_params(body: Union[str, dict]):
        if body is None or isinstance(body, str) and re.search("^\\s*$", body):
            raise exceptions.WrongParameters("No request body provided for POST /manage/v2/users!")
