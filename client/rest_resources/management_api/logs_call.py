from client.rest_resources.resource_call import ResourceCall
from client.utils import get_accept_header_for_format
import client.exceptions as exc

from dateutil import parser


class LogsCall(ResourceCall):

    ENDPOINT = "/manage/v2/logs"

    __FORMAT_PARAM = "format"
    __FILENAME_PARAM = "filename"
    __HOST_PARAM = "host"
    __START_PARAM = "start"
    __END_PARAM = "end"
    __REGEX_PARAM = "regex"

    def __init__(self, data_format: str = "html", filename: str = None, host: str = None,
                 start_time: str = None, end_time: str = None, regex: str = None):
        data_format = data_format if data_format is not None else "html"
        LogsCall.__validate_params(data_format, filename, start_time, end_time)

        super().__init__(accept=get_accept_header_for_format(data_format))
        self.add_param(LogsCall.__FORMAT_PARAM, data_format)
        self.add_param(LogsCall.__FILENAME_PARAM, filename)
        self.add_param(LogsCall.__HOST_PARAM, host)
        self.add_param(LogsCall.__START_PARAM, LogsCall.__reformat_datetime_param(start_time))
        self.add_param(LogsCall.__END_PARAM, LogsCall.__reformat_datetime_param(end_time))
        self.add_param(LogsCall.__REGEX_PARAM, regex)

    def endpoint(self):
        return LogsCall.ENDPOINT

    @staticmethod
    def __validate_params(data_format: str, filename: str, start_time: str, end_time: str):
        if data_format and data_format not in ["xml", "json", "html"]:
            raise exc.WrongParameters("The supported formats are xml, json or html")
        if not filename:
            raise exc.WrongParameters("The filename is a mandatory parameter!")
        LogsCall.__validate_datetime_param("start", start_time)
        LogsCall.__validate_datetime_param("end", end_time)

    @staticmethod
    def __validate_datetime_param(param_name: str, param_value: str):
        try:
            if param_value:
                parser.parse(param_value)
        except ValueError:
            raise exc.WrongParameters(f"The {param_name} parameter is not a dateTime value!")

    @staticmethod
    def __reformat_datetime_param(datetime_param: str):
        if datetime_param:
            return parser.parse(datetime_param).strftime("%Y-%m-%dT%H:%M:%S")
        else:
            return datetime_param
