from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class ForestGetCall(ResourceCall):
    """
    A ResourceCall implementation representing a single GET request to the /manage/v2/forests/{id|name} REST Resource

    Retrieve information about a forest. The forest can be identified either by id or name.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/forests/[id-or-name]

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/forests/{}"

    __FORMAT_PARAM = "format"
    __VIEW_PARAM = "view"

    __SUPPORTED_FORMATS = ["xml", "json", "html"]
    __SUPPORTED_VIEWS = ["describe", "default", "config", "counts", "edit",
                         "status", "storage", "xdmp:forest-status", "properties-schema"]

    def __init__(self, forest: str, data_format: str = "xml", view: str = "default"):
        """
        Parameters
        ----------
        forest : str
            A forest identifier. The forest can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
        view : str
            A specific view of the returned data.
            Can be properties-schema, config, edit, package, describe, status, xdmp:server-status or default.
        """

        data_format = data_format if data_format is not None else "xml"
        view = view if view is not None else "default"
        ForestGetCall.__validate_params(data_format, view)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        self.__forest = forest
        self.add_param(ForestGetCall.__FORMAT_PARAM, data_format)
        self.add_param(ForestGetCall.__VIEW_PARAM, view)

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Forest call

        Returns
        -------
        str
            an Forest call endpoint
        """

        return ForestGetCall.__ENDPOINT_TEMPLATE.format(self.__forest)

    @staticmethod
    def __validate_params(data_format: str, view: str):
        if data_format not in ForestGetCall.__SUPPORTED_FORMATS:
            joined_supported_formats = ", ".join(ForestGetCall.__SUPPORTED_FORMATS)
            raise exceptions.WrongParameters("The supported formats are: " + joined_supported_formats)
        if view not in ForestGetCall.__SUPPORTED_VIEWS:
            joined_supported_views = ", ".join(ForestGetCall.__SUPPORTED_VIEWS)
            raise exceptions.WrongParameters("The supported views are: " + joined_supported_views)


class ForestPostCall(ResourceCall):
    """
    A ResourceCall implementation representing a single POST request to the /manage/v2/forests/{id|name} REST Resource

    Initiate a state change on a forest, such as a merge, restart, or attach.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/POST/manage/v2/forests/[id-or-name]

    Attributes
    ----------
    ENDPOINT
        a static constant storing the Forests endpoint value

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/forests/{}"

    __STATE_PARAM = "state"

    __SUPPORTED_STATES = ["clear", "merge", "restart", "attach", "detach", "retire", "employ"]

    def __init__(self, forest: str, body: dict):
        """
        Parameters
        ----------
        forest : str
            A forest identifier. The forest can be identified either by ID or name.
        body : dict
            A list of properties. Need to include the 'state' property (the type of state change to initiate).
            Allowed values: clear, merge, restart, attach, detach, retire, employ.
        """
        ForestPostCall.__validate_params(body.get(ForestPostCall.__STATE_PARAM))
        super().__init__(method="POST",
                         content_type=constants.HEADER_X_WWW_FORM_URLENCODED,
                         body=body)
        self.__forest = forest

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Forests call

        Returns
        -------
        str
            an Forests call endpoint
        """

        return ForestPostCall.__ENDPOINT_TEMPLATE.format(self.__forest)

    @staticmethod
    def __validate_params(state: str):
        if state is None:
            raise exceptions.WrongParameters("You must include the 'state' parameter within a body!")
        elif state not in ForestPostCall.__SUPPORTED_STATES:
            joined_supported_states = ", ".join(ForestPostCall.__SUPPORTED_STATES)
            raise exceptions.WrongParameters("The supported states are: " + joined_supported_states)


class ForestDeleteCall(ResourceCall):
    """
    A ResourceCall implementation representing a single DELETE request
    to the /manage/v2/forests/{id|name} REST Resource

    Delete a forest.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/DELETE/manage/v2/forests/[id-or-name]

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/forests/{}"

    __LEVEL_PARAM = "level"
    __REPLICAS_PARAM = "replicas"

    __SUPPORTED_LEVELS = ["full", "config-only"]
    __SUPPORTED_REPLICAS_OPTS = ["detach", "delete"]

    def __init__(self, forest: str, level: str, replicas: str = None):
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
            Allowed values: detach to detach the replica but keep it; delete to detach and delete the replica.
        """
        ForestDeleteCall.__validate_params(level, replicas)
        super().__init__(method="DELETE")
        self.add_param(ForestDeleteCall.__LEVEL_PARAM, level)
        self.add_param(ForestDeleteCall.__REPLICAS_PARAM, replicas)
        self.__forest = forest

    def endpoint(self):
        """Implementation of an abstract method returning an endpoint for the Forest call

        Returns
        -------
        str
            an Forest call endpoint
        """

        return ForestDeleteCall.__ENDPOINT_TEMPLATE.format(self.__forest)

    @staticmethod
    def __validate_params(level: str, replicas: str):
        if level not in ForestDeleteCall.__SUPPORTED_LEVELS:
            joined_supported_levels = ", ".join(ForestDeleteCall.__SUPPORTED_LEVELS)
            raise exceptions.WrongParameters("The supported levels are: " + joined_supported_levels)
        if replicas and replicas not in ForestDeleteCall.__SUPPORTED_REPLICAS_OPTS:
            joined_supported_replicas_opts = ", ".join(ForestDeleteCall.__SUPPORTED_REPLICAS_OPTS)
            raise exceptions.WrongParameters("The supported replicas options are: " + joined_supported_replicas_opts)
