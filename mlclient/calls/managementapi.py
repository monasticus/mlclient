import json

from dateutil import parser

from mlclient import constants, exceptions, utils
from mlclient.calls import ResourceCall


class DatabasesCall(ResourceCall):

    ENDPOINT = "/manage/v2/databases"

    __FORMAT_PARAM = "format"
    __VIEW_PARAM = "view"

    __SUPPORTED_FORMATS = ["xml", "json", "html"]
    __SUPPORTED_VIEWS = ["describe", "default", "metrics", "package", "schema", "properties-schema"]

    def __init__(self, method: str, data_format: str = "xml", view: str = "default", body=None):
        data_format = data_format if data_format is not None else "xml"
        if data_format not in DatabasesCall.__SUPPORTED_FORMATS:
            raise exceptions.WrongParameters("The supported formats are: " + ", ".join(DatabasesCall.__SUPPORTED_FORMATS))

        super().__init__(method=method,
                         accept=utils.get_accept_header_for_format(data_format))
        if method == constants.METHOD_GET:
            self.__init_get(method, data_format, view)
        elif method == constants.METHOD_POST:
            self.__init_post(method, data_format, body)
        else:
            raise exceptions.WrongParameters("Method not allowed: the supported methods are GET and POST!")

    def endpoint(self):
        return DatabasesCall.ENDPOINT

    def __init_get(self, method: str, data_format: str, view: str):
        view = view if view is not None else "default"
        if view not in DatabasesCall.__SUPPORTED_VIEWS:
            raise exceptions.WrongParameters("The supported views are: " + ", ".join(DatabasesCall.__SUPPORTED_VIEWS))
        self.add_param(DatabasesCall.__VIEW_PARAM, view)
        self.add_param(DatabasesCall.__FORMAT_PARAM, data_format)

    def __init_post(self, method: str, data_format: str, body):
        if body is None:
            raise exceptions.WrongParameters("No request body provided for POST /manage/v2/databases!")

        content_type = utils.get_content_type_header_for_data(body)
        body = body if content_type != constants.HEADER_JSON or not isinstance(body, str) else json.loads(body)
        self.add_param(DatabasesCall.__FORMAT_PARAM, data_format)
        self.add_header(constants.HEADER_NAME_CONTENT_TYPE, content_type)
        self.set_body(body)


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
