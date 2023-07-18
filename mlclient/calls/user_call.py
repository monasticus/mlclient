
from mlclient import exceptions, utils, constants
from mlclient.calls import ResourceCall


class UserGetCall(ResourceCall):
    """
    A ResourceCall implementation representing a single GET request
    to the /manage/v2/users/{id|name} REST Resource

    This resource address returns the configuration for the specified user.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/GET/manage/v2/users/[id-or-name]

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint
    for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/users/{}"

    __FORMAT_PARAM = "format"
    __VIEW_PARAM = "view"

    __SUPPORTED_FORMATS = ["xml", "json", "html"]
    __SUPPORTED_VIEWS = ["describe", "default"]

    def __init__(
            self,
            user: str,
            data_format: str = "xml",
            view: str = "default"
    ):
        """
        Parameters
        ----------
        user : str
            A user identifier. The user can be identified either by ID or name.
        data_format : str
            The format of the returned data. Can be either html, json, or xml (default).
            This parameter is not meaningful with view=edit.
        view : str
            A specific view of the returned data. Can be: describe, or default.
        """

        data_format = data_format if data_format is not None else "xml"
        view = view if view is not None else "default"
        UserGetCall.__validate_params(data_format, view)

        super().__init__(method="GET",
                         accept=utils.get_accept_header_for_format(data_format))
        self.__user = user
        self.add_param(UserGetCall.__FORMAT_PARAM, data_format)
        self.add_param(UserGetCall.__VIEW_PARAM, view)

    def endpoint(
            self
    ):
        """Return an endpoint for the User call.

        Returns
        -------
        str
            an User call endpoint
        """

        return UserGetCall.__ENDPOINT_TEMPLATE.format(self.__user)

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


class UserDeleteCall(ResourceCall):
    """
    A ResourceCall implementation representing a single DELETE request
    to the /manage/v2/users/{id|name} REST Resource

    This resource address deletes the named user from the named security database.
    Documentation of the REST Resource API: https://docs.marklogic.com/REST/DELETE/manage/v2/users/[id-or-name]

    Methods
    -------
    All public methods are inherited from the ResourceCall abstract class.
    This class implements the endpoint() abstract method to return an endpoint
    for the specific call.
    """

    __ENDPOINT_TEMPLATE = "/manage/v2/users/{}"

    def __init__(
            self,
            user: str
    ):
        """
        Parameters
        ----------
        user : str
            A user identifier. The user can be identified either by ID or name.
        """
        super().__init__(method=constants.METHOD_DELETE)
        self.__user = user

    def endpoint(
            self
    ):
        """Return an endpoint for the User call.

        Returns
        -------
        str
            an User call endpoint
        """

        return UserDeleteCall.__ENDPOINT_TEMPLATE.format(self.__user)
