"""The ML Forest Resource Calls module.

It exports 3 classes:
    * ForestGetCall
        A GET request to get a forest details.
    * ForestPostCall
        A POST request to change a forest's state.
    * ForestDeleteCall
        A DELETE request to remove a forest.
"""
from __future__ import annotations

from typing import ClassVar

from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class ForestGetCall(ResourceCall):
    """A GET request to get a forest details.

    A ResourceCall implementation representing a single GET request
    to the /manage/v2/forests/{id|name} REST Resource.

    Retrieve information about a forest. The forest can be identified either by id
    or name.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/forests/[id-or-name]
    """

    _ENDPOINT_TEMPLATE: str = "/manage/v2/forests/{}"

    _FORMAT_PARAM: str = "format"
    _VIEW_PARAM: str = "view"

    _SUPPORTED_FORMATS: ClassVar[list] = ["xml", "json", "html"]
    _SUPPORTED_VIEWS: ClassVar[list] = ["describe", "default", "config", "counts",
                                        "edit", "status", "storage",
                                        "xdmp:forest-status", "properties-schema"]

    def __init__(
            self,
            forest: str,
            data_format: str = "xml",
            view: str = "default",
    ):
        """Initialize ForestGetCall instance.

        Parameters
        ----------
        forest : str
            A forest identifier. The forest can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data.
            Can be properties-schema, config, edit, package, describe, status,
            xdmp:server-status or default.
        """
        data_format = data_format if data_format is not None else "xml"
        view = view if view is not None else "default"
        self._validate_params(data_format, view)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        self._forest = forest
        self.add_param(self._FORMAT_PARAM, data_format)
        self.add_param(self._VIEW_PARAM, view)

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Forest call.

        Returns
        -------
        str
            A Forest call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._forest)

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


class ForestPostCall(ResourceCall):
    """A POST request to change a forest's state.

    A ResourceCall implementation representing a single POST request
    to the /manage/v2/forests/{id|name} REST Resource.

    Initiate a state change on a forest, such as a merge, restart, or attach.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/manage/v2/forests/[id-or-name]
    """

    _ENDPOINT_TEMPLATE: str = "/manage/v2/forests/{}"

    _STATE_PARAM: str = "state"

    _SUPPORTED_STATES: ClassVar[list] = ["clear", "merge", "restart", "attach",
                                         "detach", "retire", "employ"]

    def __init__(
            self,
            forest: str,
            body: dict,
    ):
        """Initialize ForestPostCall instance.

        Parameters
        ----------
        forest : str
            A forest identifier. The forest can be identified either by ID or name.
        body : dict
            A list of properties. Need to include the 'state' property (the type
            of state change to initiate).
            Allowed values: clear, merge, restart, attach, detach, retire, employ.
        """
        self._validate_params(body.get(self._STATE_PARAM))
        super().__init__(method="POST",
                         content_type=constants.HEADER_X_WWW_FORM_URLENCODED,
                         body=body)
        self._forest = forest

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
        return self._ENDPOINT_TEMPLATE.format(self._forest)

    @classmethod
    def _validate_params(
            cls,
            state: str,
    ):
        if state is None:
            msg = "You must include the 'state' parameter within a body!"
            raise exceptions.WrongParametersError(msg)
        if state not in cls._SUPPORTED_STATES:
            joined_supported_states = ", ".join(cls._SUPPORTED_STATES)
            msg = f"The supported states are: {joined_supported_states}"
            raise exceptions.WrongParametersError(msg)


class ForestDeleteCall(ResourceCall):
    """A DELETE request to remove a forest.

    A ResourceCall implementation representing a single DELETE request
    to the /manage/v2/forests/{id|name} REST Resource.

    Delete a forest.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/DELETE/manage/v2/forests/[id-or-name]
    """

    _ENDPOINT_TEMPLATE: str = "/manage/v2/forests/{}"

    _LEVEL_PARAM: str = "level"
    _REPLICAS_PARAM: str = "replicas"

    _SUPPORTED_LEVELS: ClassVar[list] = ["full", "config-only"]
    _SUPPORTED_REPLICAS_OPTS: ClassVar[list] = ["detach", "delete"]

    def __init__(
            self,
            forest: str,
            level: str,
            replicas: str | None = None,
    ):
        """Initialize ForestDeleteCall instance.

        Parameters
        ----------
        forest : str
            A forest identifier. The forest can be identified either by ID or name.
        level : str
            The type of state change to initiate. Allowed values: full, config-only.
            A config-only deletion removes only the forest configuration;
            the data contained in the forest remains on disk.
            A full deletion removes both the forest configuration and the data.
        replicas : str
            Determines how to process the replicas.
            Allowed values: detach to detach the replica but keep it; delete to detach
            and delete the replica.
        """
        self._validate_params(level, replicas)
        super().__init__(method=constants.METHOD_DELETE)
        self.add_param(self._LEVEL_PARAM, level)
        self.add_param(self._REPLICAS_PARAM, replicas)
        self._forest = forest

    @property
    def endpoint(
            self,
    ):
        """An endpoint for the Forest call.

        Returns
        -------
        str
            A Forest call endpoint
        """
        return self._ENDPOINT_TEMPLATE.format(self._forest)

    @classmethod
    def _validate_params(
            cls,
            level: str,
            replicas: str,
    ):
        if level not in cls._SUPPORTED_LEVELS:
            joined_supported_levels = ", ".join(cls._SUPPORTED_LEVELS)
            msg = f"The supported levels are: {joined_supported_levels}"
            raise exceptions.WrongParametersError(msg)
        if replicas and replicas not in cls._SUPPORTED_REPLICAS_OPTS:
            joined_supported_opts = ", ".join(cls._SUPPORTED_REPLICAS_OPTS)
            msg = f"The supported replicas options are: {joined_supported_opts}"
            raise exceptions.WrongParametersError(msg)
