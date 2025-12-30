import pytest


# set anyio backend for tests
# https://anyio.readthedocs.io/en/stable/testing.html#specifying-the-backends-to-run-on
#
# set scope to module to enable usage of module scoped async client fixture
# https://anyio.readthedocs.io/en/stable/testing.html#using-async-fixtures-with-higher-scopes
@pytest.fixture(scope="module")
def anyio_backend() -> str:
    return "asyncio"
