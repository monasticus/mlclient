from dateutil import parser

from mlclient import exceptions, utils
from mlclient.calls import ResourceCall


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
                         accept=utils.get_accept_header_for_format(resp_format))
        self.__resp_format = resp_format
        self.add_param(DatabasesCall.__FORMAT_PARAM, resp_format)
        self.add_param(DatabasesCall.__VIEW_PARAM, view)

    def endpoint(self):
        return DatabasesCall.ENDPOINT

    @staticmethod
    def __validate_params(method, resp_format, view):
        if method not in ["GET", "POST"]:
            raise exceptions.WrongParameters("Method not allowed: the supported methods are GET and POST!")
        if resp_format not in DatabasesCall.__SUPPORTED_FORMATS:
            raise exceptions.WrongParameters("The supported formats are: " + ", ".join(DatabasesCall.__SUPPORTED_FORMATS))
        if view not in DatabasesCall.__SUPPORTED_VIEWS:
            raise exceptions.WrongParameters("The supported views are: " + ", ".join(DatabasesCall.__SUPPORTED_VIEWS))


class LogsCall(ResourceCall):

    ENDPOINT = "/manage/v2/logs"

    __FORMAT_PARAM = "format"
    __FILENAME_PARAM = "filename"
    __HOST_PARAM = "host"
    __START_PARAM = "start"
    __END_PARAM = "end"
    __REGEX_PARAM = "regex"

    def __init__(self, filename: str, data_format: str = "html", host: str = None,
                 start_time: str = None, end_time: str = None, regex: str = None):
        data_format = data_format if data_format is not None else "html"
        LogsCall.__validate_params(data_format, start_time, end_time)

        super().__init__(accept=utils.get_accept_header_for_format(data_format))
        self.add_param(LogsCall.__FORMAT_PARAM, data_format)
        self.add_param(LogsCall.__FILENAME_PARAM, filename)
        self.add_param(LogsCall.__HOST_PARAM, host)
        self.add_param(LogsCall.__START_PARAM, LogsCall.__reformat_datetime_param(start_time))
        self.add_param(LogsCall.__END_PARAM, LogsCall.__reformat_datetime_param(end_time))
        self.add_param(LogsCall.__REGEX_PARAM, regex)

    def endpoint(self):
        return LogsCall.ENDPOINT

    @staticmethod
    def __validate_params(data_format: str, start_time: str, end_time: str):
        if data_format and data_format not in ["xml", "json", "html"]:
            raise exceptions.WrongParameters("The supported formats are xml, json or html!")
        LogsCall.__validate_datetime_param("start", start_time)
        LogsCall.__validate_datetime_param("end", end_time)

    @staticmethod
    def __validate_datetime_param(param_name: str, param_value: str):
        try:
            if param_value:
                parser.parse(param_value)
        except ValueError:
            raise exceptions.WrongParameters(f"The {param_name} parameter is not a dateTime value!")

    @staticmethod
    def __reformat_datetime_param(datetime_param: str):
        if datetime_param:
            return parser.parse(datetime_param).strftime("%Y-%m-%dT%H:%M:%S")
        else:
            return datetime_param
