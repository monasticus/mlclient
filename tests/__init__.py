import pytest

# Rewrite assertions from the test utils module
pytest.register_assert_rewrite("tests.tools")
pytest.register_assert_rewrite("tests.utils")
