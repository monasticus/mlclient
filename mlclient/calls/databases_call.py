"""The ML Databases Resource Calls module.

It exports 2 classes:
    * DatabasesGetCall
        A GET request to get databases summary.
    * DatabasesPostCall
        A POST request to create a new database.
"""
from __future__ import annotations

import json
import re
from typing import ClassVar

from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class DatabasesGetCall(ResourceCall):
    """A GET request to get databases summary.

    A ResourceCall implementation representing a single GET request
    to the /manage/v2/databases REST Resource.

    This resource address returns a summary of the databases in the cluster.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/databases
    """

    _ENDPOINT: str = "/manage/v2/databases"

    _FORMAT_PARAM: str = "format"
    _VIEW_PARAM: str = "view"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]
    _SUPPORTED_VIEWS: ClassVar[list] = ["describe", "default", "metrics", "package",
                                        "schema", "properties-schema"]

    def __init__(
            self,
            data_format: str = "xml",
            view: str = "default",
    ):
        """Initialize DatabasesGetCall instance.

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data.
            Can be schema, properties-schema, metrics, package, describe, or default.
        """
        data_format = data_format if data_format is not None else "xml"
        view = view if view is not None else "default"
        self._validate_params(data_format, view)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        self.add_param(self._FORMAT_PARAM, data_format)
        self.add_param(self._VIEW_PARAM, view)

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Databases call.

        Returns
        -------
        str
            A Databases call endpoint
        """
        return self._ENDPOINT

    @classmethod
    def _validate_params(
            cls,
            data_format: str,
            view: str,
    ):
        if data_format not in cls._SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(cls._SUPPORTED_FORMATS)
            msg = f"The supported formats are: {joined_supported_formats}"
            raise exceptions.WrongParametersError(msg)
        if view not in cls._SUPPORTED_VIEWS:
            joined_supported_views = ", ".join(cls._SUPPORTED_VIEWS)
            msg = f"The supported views are: {joined_supported_views}"
            raise exceptions.WrongParametersError(msg)


class DatabasesPostCall(ResourceCall):
    """A POST request to create a new database.

    A ResourceCall implementation representing a single POST request
    to the /manage/v2/databases REST Resource.

    This resource address creates a new database in the cluster.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/manage/v2/databases
    """

    _ENDPOINT: str = "/manage/v2/databases"

    def __init__(
            self,
            body: str | dict,
    ):
        """Initialize DatabasesPostCall instance.

        Parameters
        ----------
        body : str | dict
            A database properties in XML or JSON format.
        """
        self._validate_params(body)
        content_type = utils.get_content_type_header_for_data(body)
        if content_type == constants.HEADER_JSON and isinstance(body, str):
            body = json.loads(body)
        super().__init__(method="POST",
                         content_type=content_type,
                         body=body)

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Databases call.

        Returns
        -------
        str
            A Databases call endpoint
        """
        return self._ENDPOINT

    @classmethod
    def _validate_params(
            cls,
            body: str | dict,
    ):
        if body is None or isinstance(body, str) and re.search("^\\s*$", body):
            msg = "No request body provided for POST /manage/v2/databases!"
            raise exceptions.WrongParametersError(msg)
