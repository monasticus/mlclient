import pytest

from tests.utils.resources import discover_query_cases, render_test_resource


def test_xquery_fragments_preserve_braces_variables_and_inserted_markers():
    assert render_test_resource(
        __file__,
        "template.xqy",
        body="$value",
        name="@@body@@",
    ) == (
        'declare variable $value external;\nelement {"result"} { $value, "@@body@@" }\n'
    )


@pytest.mark.parametrize("fragments", [{}, {"body": "1", "name": "x", "extra": "2"}])
def test_xquery_fragments_must_match_the_template(fragments):
    with pytest.raises(ValueError, match="Expected fragments"):
        render_test_resource(__file__, "template.xqy", **fragments)


def test_resource_cases_expand_parameters_and_run_with_fixtures(
    tmp_path, mocker, request,
):
    case = tmp_path / "parameterized"
    case.mkdir()
    (case / "case.py").write_text(
        "import pytest\n"
        '@pytest.mark.parametrize("value", '
        '[{"a": 1}, pytest.param({"a": 1}, id="named")])\n'
        "def run(value, tmp_path):\n"
        '    assert value == {"a": 1}\n'
        "    assert tmp_path.is_dir()\n",
    )
    mocker.patch(
        "tests.utils.resources.get_test_resources_path", return_value=str(tmp_path),
    )
    cases = discover_query_cases(__file__)
    assert len(cases) == 2
    for item in cases:
        item.assert_matches(request)


def test_resource_cases_reject_an_empty_directory(tmp_path, mocker):
    mocker.patch(
        "tests.utils.resources.get_test_resources_path", return_value=str(tmp_path),
    )
    with pytest.raises(ValueError, match="No query cases"):
        discover_query_cases(__file__)


def test_resource_cases_require_a_callable(tmp_path, mocker):
    case = tmp_path / "invalid"
    case.mkdir()
    (case / "case.py").write_text("run = None\n")
    mocker.patch(
        "tests.utils.resources.get_test_resources_path", return_value=str(tmp_path),
    )
    with pytest.raises(TypeError, match="must define run"):
        discover_query_cases(__file__)
