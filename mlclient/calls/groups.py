"""The ML Group Api Calls module.

This module provides call classes for group-related REST resources.

It exports 2 classes:
    * GroupPropertiesGetCall
        A GET request to get group properties.
    * GroupPropertiesPutCall
        A PUT request to modify group properties.
"""

from __future__ import annotations

import json
import re
from typing import ClassVar

from mlclient import constants, exceptions, utils
from mlclient.calls.api_call import ApiCall


class GroupPropertiesGetCall(ApiCall):
    """A GET request to get group properties.

    An ApiCall implementation representing a single GET request
    to the /manage/v2/groups/{id|name}/properties endpoint.

    This resource address returns the current state of modifiable properties
    of the specified group.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/GET/manage/v2/groups/[id-or-name]/properties
    """

    _API_VERSION: int = 2

    _ENDPOINT_TEMPLATE: str = "/manage/v{}/groups/{}/properties"

    _FORMAT_PARAM: str = "format"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]

    def __init__(
        self,
        group: str,
        data_format: str = "xml",
    ):
        """Initialize GroupPropertiesGetCall instance.

        Parameters
        ----------
        group : str
            A group identifier. The group can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be html, json or xml (default).
            This parameter overrides the Accept header if both are present.
        """
        data_format = data_format if data_format is not None else "xml"
        self._validate_params(data_format)

        super().__init__(
            method="GET",
            accept=utils.get_accept_header_for_format(data_format),
        )
        self._group = group
        self.add_param(self._FORMAT_PARAM, data_format)

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Group Properties call.

        Returns
        -------
        str
            A Group Properties call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._group)

    @classmethod
    def _validate_params(
        cls,
        data_format: str,
    ):
        """Validate the response format.

        Parameters
        ----------
        data_format : str
            Requested response format

        Raises
        ------
        WrongParametersError
            If the format is not xml, json or html
        """
        if data_format not in cls._SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(cls._SUPPORTED_FORMATS)
            msg = f"The supported formats are: {joined_supported_formats}"
            raise exceptions.WrongParametersError(msg)


class GroupPropertiesPutCall(ApiCall):
    """A PUT request to modify group properties.

    An ApiCall implementation representing a single PUT request
    to the /manage/v2/groups/{id|name}/properties endpoint.

    Initiate a properties change on the specified group.
    Documentation of the REST Resource API:
    https://docs.marklogic.com/REST/PUT/manage/v2/groups/[id-or-name]/properties
    """

    _API_VERSION: int = 2

    _ENDPOINT_TEMPLATE: str = "/manage/v{}/groups/{}/properties"

    def __init__(
        self,
        group: str,
        body: str | dict,
    ):
        """Initialize GroupPropertiesPutCall instance.

        Parameters
        ----------
        group : str
            A group identifier. The group can be identified either by ID or name.
        body : str | dict
            Group properties in XML or JSON format.
        """
        self._validate_params(body)
        content_type = utils.get_content_type_header_for_data(body)
        if content_type == constants.HEADER_JSON and isinstance(body, str):
            body = json.loads(body)
        super().__init__(method="PUT", content_type=content_type, body=body)
        self._group = group

    @property
    def endpoint(
        self,
    ):
        """An endpoint for the Group Properties call.

        Returns
        -------
        str
            A Group Properties call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._API_VERSION, self._group)

    @classmethod
    def _validate_params(
        cls,
        body: str | dict,
    ):
        """Reject missing or blank property documents.

        Parameters
        ----------
        body : str | dict
            Property document to send

        Raises
        ------
        WrongParametersError
            If no request body was provided
        """
        if body is None or (isinstance(body, str) and re.search("^\\s*$", body)):
            msg = (
                "No request body provided for "
                "PUT /manage/v2/groups/{id|name}/properties!"
            )
            raise exceptions.WrongParametersError(msg)
