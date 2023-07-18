from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class ForestGetCall(ResourceCall):
    """
    A ResourceCall implementation representing a single GET request
    to the /manage/v2/forests/{id|name} REST Resource

    Retrieve information about a forest. The forest can be identified either by id
    or name.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/forests/[id-or-name]

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint
    for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/forests/{}"

    __FORMAT_PARAM = "format"
    __VIEW_PARAM = "view"

    __SUPPORTED_FORMATS = ["xml", "json", "html"]
    __SUPPORTED_VIEWS = ["describe", "default", "config", "counts", "edit",
                         "status", "storage", "xdmp:forest-status", "properties-schema"]

    def __init__(
            self,
            forest: str,
            data_format: str = "xml",
            view: str = "default"
    ):
        """
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
        ForestGetCall.__validate_params(data_format, view)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        self.__forest = forest
        self.add_param(ForestGetCall.__FORMAT_PARAM, data_format)
        self.add_param(ForestGetCall.__VIEW_PARAM, view)

    def endpoint(
            self
    ):
        """Return an endpoint for the Forest call.

        Returns
        -------
        str
            an Forest call endpoint
        """

        return ForestGetCall.__ENDPOINT_TEMPLATE.format(self.__forest)

    @classmethod
    def __validate_params(
            cls,
            data_format: str,
            view: str
    ):
        if data_format not in cls.__SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(cls.__SUPPORTED_FORMATS)
            msg = f"The supported formats are: {joined_supported_formats}"
            raise exceptions.WrongParameters(msg)
        if view not in cls.__SUPPORTED_VIEWS:
            joined_supported_views = ", ".join(cls.__SUPPORTED_VIEWS)
            msg = f"The supported views are: {joined_supported_views}"
            raise exceptions.WrongParameters(msg)


class ForestPostCall(ResourceCall):
    """
    A ResourceCall implementation representing a single POST request
    to the /manage/v2/forests/{id|name} REST Resource

    Initiate a state change on a forest, such as a merge, restart, or attach.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/manage/v2/forests/[id-or-name]

    Attributes
    ----------
    ENDPOINT
        a static constant storing the Forests endpoint value

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint
    for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/forests/{}"

    __STATE_PARAM = "state"

    __SUPPORTED_STATES = ["clear", "merge", "restart", "attach", "detach", "retire",
                          "employ"]

    def __init__(
            self,
            forest: str,
            body: dict
    ):
        """
        Parameters
        ----------
        forest : str
            A forest identifier. The forest can be identified either by ID or name.
        body : dict
            A list of properties. Need to include the 'state' property (the type
            of state change to initiate).
            Allowed values: clear, merge, restart, attach, detach, retire, employ.
        """
        ForestPostCall.__validate_params(body.get(ForestPostCall.__STATE_PARAM))
        super().__init__(method="POST",
                         content_type=constants.HEADER_X_WWW_FORM_URLENCODED,
                         body=body)
        self.__forest = forest

    def endpoint(
            self
    ):
        """Return an endpoint for the Forests call.

        Returns
        -------
        str
            an Forests call endpoint
        """

        return ForestPostCall.__ENDPOINT_TEMPLATE.format(self.__forest)

    @classmethod
    def __validate_params(
            cls,
            state: str
    ):
        if state is None:
            msg = "You must include the 'state' parameter within a body!"
            raise exceptions.WrongParameters(msg)
        elif state not in cls.__SUPPORTED_STATES:
            joined_supported_states = ", ".join(cls.__SUPPORTED_STATES)
            msg = f"The supported states are: {joined_supported_states}"
            raise exceptions.WrongParameters(msg)


class ForestDeleteCall(ResourceCall):
    """
    A ResourceCall implementation representing a single DELETE request
    to the /manage/v2/forests/{id|name} REST Resource

    Delete a forest.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/DELETE/manage/v2/forests/[id-or-name]

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint
    for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/forests/{}"

    __LEVEL_PARAM = "level"
    __REPLICAS_PARAM = "replicas"

    __SUPPORTED_LEVELS = ["full", "config-only"]
    __SUPPORTED_REPLICAS_OPTS = ["detach", "delete"]

    def __init__(
            self,
            forest: str,
            level: str,
            replicas: str = None
    ):
        """
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
        ForestDeleteCall.__validate_params(level, replicas)
        super().__init__(method=constants.METHOD_DELETE)
        self.add_param(ForestDeleteCall.__LEVEL_PARAM, level)
        self.add_param(ForestDeleteCall.__REPLICAS_PARAM, replicas)
        self.__forest = forest

    def endpoint(
            self
    ):
        """Return an endpoint for the Forest call.

        Returns
        -------
        str
            an Forest call endpoint
        """

        return ForestDeleteCall.__ENDPOINT_TEMPLATE.format(self.__forest)

    @classmethod
    def __validate_params(
            cls,
            level: str,
            replicas: str
    ):
        if level not in cls.__SUPPORTED_LEVELS:
            joined_supported_levels = ", ".join(cls.__SUPPORTED_LEVELS)
            msg = f"The supported levels are: {joined_supported_levels}"
            raise exceptions.WrongParameters(msg)
        if replicas and replicas not in cls.__SUPPORTED_REPLICAS_OPTS:
            joined_supported_opts = ", ".join(cls.__SUPPORTED_REPLICAS_OPTS)
            msg = f"The supported replicas options are: {joined_supported_opts}"
            raise exceptions.WrongParameters(msg)
