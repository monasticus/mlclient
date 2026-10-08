import sys

import pytest

from mlclient.xquery import Cts, XqyExpression


def test_abstract_expression_requires_render():
    with pytest.raises(TypeError) as error:
        XqyExpression()

    expected_message = (
        "Can't instantiate abstract class XqyExpression with abstract method render"
        if sys.version_info < (3, 12)
        else (
            "Can't instantiate abstract class XqyExpression without an "
            "implementation for abstract method 'render'"
        )
    )
    assert str(error.value) == expected_message


def test_expression_string_contains_complete_source():
    assert str(Cts.uris()) == 'xquery version "1.0-ml";\ncts:uris()'
