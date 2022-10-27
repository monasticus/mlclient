from client import exceptions
from client.rest_resources.management_api.logs_call import LogsCall
from datetime import datetime
import pytest


@pytest.fixture
def default_logs_call():
    """Returns an LogsCall instance with a required parameter without any custom details"""
    return LogsCall(filename="ErrorLogs.txt")


def test_validation_unsupported_format():
    with pytest.raises(exceptions.WrongParameters) as err:
        LogsCall(filename="", data_format="text")

    assert err.value.args[0] == "The supported formats are xml, json or html!"


def test_validation_start_time_is_not_datetime_value():
    with pytest.raises(exceptions.WrongParameters) as err:
        assert LogsCall(filename="", start_time="a").params() == {}

    assert err.value.args[0] == "The start parameter is not a dateTime value!"


def test_validation_end_time_is_not_datetime_value():
    with pytest.raises(exceptions.WrongParameters) as err:
        assert LogsCall(filename="", end_time="a").params() == {}

    assert err.value.args[0] == "The end parameter is not a dateTime value!"


def test_endpoint(default_logs_call):
    assert default_logs_call.endpoint() == "/manage/v2/logs"
    assert default_logs_call.ENDPOINT == "/manage/v2/logs"
    assert LogsCall.ENDPOINT == "/manage/v2/logs"


def test_method(default_logs_call):
    assert default_logs_call.method() == "GET"


def test_headers_for_default_format():
    call = LogsCall(filename="ErrorLogs.txt")
    assert {
        "accept": "text/html"
    } == call.headers()


def test_headers_for_none_format():
    call = LogsCall(filename="ErrorLogs.txt", data_format=None)
    assert {
        "accept": "text/html"
    } == call.headers()


def test_headers_for_html_format():
    call = LogsCall(filename="ErrorLogs.txt", data_format="html")
    assert {
        "accept": "text/html"
    } == call.headers()


def test_headers_for_xml_format():
    call = LogsCall(filename="ErrorLogs.txt", data_format="xml")
    assert {
        "accept": "application/xml"
    } == call.headers()


def test_headers_for_json_format():
    call = LogsCall(filename="ErrorLogs.txt", data_format="json")
    assert {
        "accept": "application/json"
    } == call.headers()


def test_body(default_logs_call):
    assert default_logs_call.body() is None


def test_fully_parametrized_call():
    call = LogsCall(filename="ErrorLogs.txt",
                    data_format="json",
                    host="localhost",
                    start_time="2022-01-01 01:01:01",
                    end_time="2022-01-01 01:02:02",
                    regex="some-re")
    assert call.method() == "GET"
    assert {
        "accept": "application/json"
    } == call.headers()
    assert {
         "filename": "ErrorLogs.txt",
         "format": "json",
         "host": "localhost",
         "start": "2022-01-01T01:01:01",
         "end": "2022-01-01T01:02:02",
         "regex": "some-re"
    } == call.params()
    assert call.body() is None


def test_formatting_datetime_basic():
    params = LogsCall(filename="ErrorLogs.txt",
                      start_time="2022-01-01 01:01:01").params()
    assert params["start"] == "2022-01-01T01:01:01"


def test_formatting_datetime_year_only():
    params = LogsCall(filename="ErrorLogs.txt",
                      start_time="2020").params()
    now = datetime.now()
    assert params["start"] == f"2020-{now.month}-{now.day}T00:00:00"


def test_formatting_datetime_partial_year_only():
    params = LogsCall(filename="ErrorLogs.txt",
                      start_time="32").params()
    now = datetime.now()
    assert params["start"] == f"2032-{now.month}-{now.day}T00:00:00"


def test_formatting_datetime_day_only():
    params = LogsCall(filename="ErrorLogs.txt",
                      start_time="28").params()
    now = datetime.now()
    assert params["start"] == f"{now.year}-{now.month}-28T00:00:00"


def test_formatting_datetime_month_and_day():
    params = LogsCall(filename="ErrorLogs.txt",
                      start_time="01-01").params()
    now = datetime.now()
    assert params["start"] == f"{now.year}-01-01T00:00:00"


def test_formatting_datetime_year_month_and_day():
    params = LogsCall(filename="ErrorLogs.txt",
                      start_time="1999-01-01").params()
    assert params["start"] == "1999-01-01T00:00:00"


def test_formatting_datetime_time_only():
    params = LogsCall(filename="ErrorLogs.txt",
                      start_time="01:01").params()
    now = datetime.now()
    assert params["start"] == f"{now.year}-{now.month}-{now.day}T01:01:00"


def test_formatting_datetime_time_only_with_seconds():
    params = LogsCall(filename="ErrorLogs.txt",
                      start_time="01:01:01").params()
    now = datetime.now()
    assert params["start"] == f"{now.year}-{now.month}-{now.day}T01:01:01"


def test_formatting_datetime_time_only_with_seconds_and_millis():
    params = LogsCall(filename="ErrorLogs.txt",
                      start_time="01:01:01.001").params()
    now = datetime.now()
    assert params["start"] == f"{now.year}-{now.month}-{now.day}T01:01:01"


def test_formatting_datetime_date_and_hour_only():
    params = LogsCall(filename="ErrorLogs.txt",
                      start_time="2022-01-01 01").params()
    assert params["start"] == "2022-01-01T01:00:00"


def test_formatting_datetime_date_and_time():
    params = LogsCall(filename="ErrorLogs.txt",
                      start_time="2022-01-01 01:01").params()
    assert params["start"] == "2022-01-01T01:01:00"


def test_formatting_datetime_date_and_time_with_seconds():
    params = LogsCall(filename="ErrorLogs.txt",
                      start_time="2022-01-01 01:01:01").params()
    assert params["start"] == "2022-01-01T01:01:01"


def test_formatting_datetime_date_and_time_with_seconds_and_millis():
    params = LogsCall(filename="ErrorLogs.txt",
                      start_time="2022-01-01 01:01:01.001").params()
    assert params["start"] == "2022-01-01T01:01:01"


def test_formatting_datetime_impossible_to_parse_as_month_and_day():
    with pytest.raises(exceptions.WrongParameters) as err:
        assert LogsCall(filename="ErrorLogs.txt",
                        start_time="13-01").params() == {}

    assert err.value.args[0] == "The start parameter is not a dateTime value!"


def test_formatting_datetime_impossible_to_parse_as_time_1():
    with pytest.raises(exceptions.WrongParameters) as err:
        assert LogsCall(filename="ErrorLogs.txt",
                        start_time="25:01").params() == {}

    assert err.value.args[0] == "The start parameter is not a dateTime value!"


def test_formatting_datetime_impossible_to_parse_as_time_2():
    with pytest.raises(exceptions.WrongParameters) as err:
        assert LogsCall(filename="ErrorLogs.txt",
                        start_time="24:00").params() == {}

    assert err.value.args[0] == "The start parameter is not a dateTime value!"


def test_formatting_datetime_impossible_to_parse_as_time_3():
    with pytest.raises(exceptions.WrongParameters) as err:
        assert LogsCall(filename="ErrorLogs.txt",
                        start_time="01:60").params() == {}

    assert err.value.args[0] == "The start parameter is not a dateTime value!"
