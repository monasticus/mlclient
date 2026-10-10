import pytest
from mlclient.search.structured import sq


def run():
    with pytest.raises(TypeError, match=r"""NearQuery.distance must be an integer"""):
        sq.near(sq.term("blue"), distance=1.5)
