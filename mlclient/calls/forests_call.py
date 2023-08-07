"""The ML Forests Resource Calls module.

It exports 3 classes:
    * ForestsGetCall
        A GET request to get forests summary.
    * ForestsPostCall
        A POST request to create a new forest.
    * ForestsPutCall
        A PUT request to perform an operation on forests.
"""
from __future__ import annotations

import json
import re
from typing import ClassVar

from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class ForestsGetCall(ResourceCall):
    """A GET request to get forests summary.

    A ResourceCall implementation representing a single GET request
    to the /manage/v2/forests REST Resource.

    This resource address returns data about the forests in the cluster.
    The data returned depends on the view.
    If no view is specified, this request returns a summary of the forests
    in the cluster.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/forests
    """

    _ENDPOINT: str = "/manage/v2/forests"

    _FORMAT_PARAM: str = "format"
    _VIEW_PARAM: str = "view"
    _DATABASE_ID_PARAM: str = "database-id"
    _GROUP_ID_PARAM: str = "group-id"
    _HOST_ID_PARAM: str = "host-id"
    _FULL_REFS_PARAM: str = "fullrefs"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]
    _SUPPORTED_VIEWS: ClassVar[list] = ["describe", "default", "status", "metrics",
                                        "schema", "storage", "properties-schema"]

    def __init__(
            self,
            data_format: str = "xml",
            view: str = "default",
            database: str | None = None,
            group: str | None = None,
            host: str | None = None,
            full_refs: bool | None = None,
    ):
        """Initialize ForestsGetCall instance.

        Parameters
        ----------
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data.
            Can be either describe, default, status, metrics, schema, storage,
            or properties-schema.
        database : str
            Returns a summary of the forests for the specified database.
            The database can be identified either by id or name.
        group : str
            Returns a summary of the forests for the specified group.
            The group can be identified either by id or name.
        host : str
            Returns a summary of the forests for the specified host.
            The host can be identified either by id or name.
        full_refs : bool
            If set to true, full detail is returned for all relationship references.
            A value of false (the default) indicates to return detail only for first
            references.
        """
        data_format = data_format if data_format is not None else "xml"
        view = view if view is not None else "default"
        self._validate_params(data_format, view)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        if full_refs is not None:
            full_refs = str(full_refs).lower()
        self.add_param(self._FORMAT_PARAM, data_format)
        self.add_param(self._VIEW_PARAM, view)
        self.add_param(self._DATABASE_ID_PARAM, database)
        self.add_param(self._GROUP_ID_PARAM, group)
        self.add_param(self._HOST_ID_PARAM, host)
        self.add_param(self._FULL_REFS_PARAM, full_refs)

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Forests call.

        Returns
        -------
        str
            A Forests call endpoint
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


class ForestsPostCall(ResourceCall):
    """A POST request to create a new forest.

    A ResourceCall implementation representing a single POST request
    to the /manage/v2/forests REST Resource.

    Create a new forest, including replicas if specified.
    If a database id or database is included, attach the new forest(s) to the database.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/manage/v2/forests
    """

    _ENDPOINT: str = "/manage/v2/forests"

    _WAIT_FOR_FOREST_TO_MOUNT_PARAM: str = "wait-for-forest-to-mount"

    def __init__(
            self,
            body: str | dict,
            wait_for_forest_to_mount: bool | None = None,
    ):
        """Initialize ForestsPostCall instance.

        Parameters
        ----------
        body : str | dict
            A database properties in XML or JSON format.
        wait_for_forest_to_mount : bool
            Whether to wait for the new forest to mount before sending a response
            to this request. Allowed values: true (default) or false.
        """
        self._validate_params(body)
        content_type = utils.get_content_type_header_for_data(body)
        if content_type == constants.HEADER_JSON and isinstance(body, str):
            body = json.loads(body)
        super().__init__(method="POST",
                         content_type=content_type,
                         body=body)
        if wait_for_forest_to_mount is not None:
            wait_for_forest_to_mount = str(wait_for_forest_to_mount).lower()
        self.add_param(self._WAIT_FOR_FOREST_TO_MOUNT_PARAM,
                       wait_for_forest_to_mount)

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Forests call.

        Returns
        -------
        str
            A Forests call endpoint
        """
        return self._ENDPOINT

    @classmethod
    def _validate_params(
            cls,
            body: str | dict,
    ):
        if body is None or isinstance(body, str) and re.search("^\\s*$", body):
            msg = "No request body provided for POST /manage/v2/forests!"
            raise exceptions.WrongParametersError(msg)


class ForestsPutCall(ResourceCall):
    """A PUT request to perform an operation on forests.

    A ResourceCall implementation representing a single PUT request
    to the /manage/v2/forests REST Resource.

    Perform an operation on one or more forests, such as combining multiple forests
    into a single new one, or migrating the data in the forests to a new data directory.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/PUT/manage/v2/forests
    """

    _ENDPOINT: str = "/manage/v2/forests"

    def __init__(
            self,
            body: str | dict,
    ):
        """Initialize ForestsPutCall instance.

        Parameters
        ----------
        body : str | dict
            A database properties in XML or JSON format.
        """
        self._validate_params(body)
        content_type = utils.get_content_type_header_for_data(body)
        if content_type == constants.HEADER_JSON and isinstance(body, str):
            body = json.loads(body)
        super().__init__(method="PUT",
                         content_type=content_type,
                         body=body)

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Forests call.

        Returns
        -------
        str
            A Forests call endpoint
        """
        return self._ENDPOINT

    @classmethod
    def _validate_params(
            cls,
            body: str | dict,
    ):
        if body is None or isinstance(body, str) and re.search("^\\s*$", body):
            msg = "No request body provided for PUT /manage/v2/forests!"
            raise exceptions.WrongParametersError(msg)
