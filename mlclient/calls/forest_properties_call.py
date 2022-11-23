import json
import re
from typing import Union

from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class ForestPropertiesGetCall(ResourceCall):
    """
    A ResourceCall implementation representing a single GET request
    to the /manage/v2/forests/{id|name}/properties REST Resource

    Retrieve the current state of modifiable properties of the forest identified by {id|name}.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/GET/manage/v2/forests/[id-or-name]/properties

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/forests/{}/properties"

    __FORMAT_PARAM = "format"

    __SUPPORTED_FORMATS = ["xml", "json", "html"]

    def __init__(self, forest: str, data_format: str = "xml"):
        """
        Parameters
        ----------
        forest : str
            A forest identifier. The forest can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either json or xml (default).
            This parameter overrides the Accept header if both are present.
        """

        data_format = data_format if data_format is not None else "xml"
        ForestPropertiesGetCall.__validate_params(data_format)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        self.__forest = forest
        self.add_param(ForestPropertiesGetCall.__FORMAT_PARAM, data_format)

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Forest Properties call

        Returns
        -------
        str
            a Forest Properties call endpoint
        """

        return ForestPropertiesGetCall.__ENDPOINT_TEMPLATE.format(self.__forest)

    @staticmethod
    def __validate_params(data_format: str):
        if data_format not in ForestPropertiesGetCall.__SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(ForestPropertiesGetCall.__SUPPORTED_FORMATS)
            raise exceptions.WrongParameters("The supported formats are: " + joined_supported_formats)


class ForestPropertiesPutCall(ResourceCall):
    """
    A ResourceCall implementation representing a single PUT request
    to the /manage/v2/forests/{id|name}/properties REST Resource

    Modify the configuration of the forest identified by {id|name}.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/PUT/manage/v2/forests/[id-or-name]/properties

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/forests/{}/properties"

    def __init__(self, forest: str, body: Union[str, dict]):
        """
        Parameters
        ----------
        forest : str
            A forest identifier. The forest can be identified either by ID or name.
        body : Union[str, dict]
            A forest properties in XML or JSON format.
        """
        ForestPropertiesPutCall.__validate_params(body)
        content_type = utils.get_content_type_header_for_data(body)
        body = body if content_type != constants.HEADER_JSON or not isinstance(body, str) else json.loads(body)
        super().__init__(method="PUT",
                         content_type=content_type,
                         body=body)
        self.__forest = forest

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Forest Properties call

        Returns
        -------
        str
            a Forest Properties call endpoint
        """

        return ForestPropertiesPutCall.__ENDPOINT_TEMPLATE.format(self.__forest)

    @staticmethod
    def __validate_params(body: Union[str, dict]):
        if body is None or isinstance(body, str) and re.search("^\\s*$", body):
            raise exceptions.WrongParameters("No request body provided for "
                                             "PUT /manage/v2/forests/{id|name}/properties!")
