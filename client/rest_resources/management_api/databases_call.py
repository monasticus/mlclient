from client.rest_resources.resource_call import ResourceCall
from client.utils import get_accept_header_for_format
import client.exceptions as exc


class DatabasesCall(ResourceCall):

    ENDPOINT = "/manage/v2/databases"

    __FORMAT_PARAM = "format"
    __VIEW_PARAM = "view"

    __SUPPORTED_FORMATS = ["xml", "json", "html"]
    __SUPPORTED_VIEWS = ["describe", "default", "metrics", "package", "schema", "properties-schema"]

    def __init__(self, method: str, resp_format: str = "xml", view: str = "default"):
        resp_format = resp_format if resp_format is not None else "xml"
        view = view if view is not None else "default"
        DatabasesCall.__validate_params(method, resp_format, view)

        super().__init__(method=method,
                         accept=get_accept_header_for_format(resp_format))
        self.__resp_format = resp_format
        self.add_param(DatabasesCall.__FORMAT_PARAM, resp_format)
        self.add_param(DatabasesCall.__VIEW_PARAM, view)

    def endpoint(self):
        return DatabasesCall.ENDPOINT

    @staticmethod
    def __validate_params(method, resp_format, view):
        if method not in ["GET", "POST"]:
            raise exc.WrongParameters("Method not allowed: the supported methods are GET and POST!")
        if resp_format not in DatabasesCall.__SUPPORTED_FORMATS:
            raise exc.WrongParameters("The supported formats are:")
        if view not in DatabasesCall.__SUPPORTED_VIEWS:
            raise exc.WrongParameters("The supported views are: " + ", ".join(DatabasesCall.__SUPPORTED_VIEWS))
