from typing import Literal

import pytest

from mountory_core.testing.utils import random_url, random_http_url


def test_random_url_defaults_to_http() -> None:
    url = random_url()

    assert url.scheme == "http"


@pytest.mark.parametrize("scheme", ("http", "https"))
def test_random_url_sets_scheme(scheme: Literal["http", "https"]) -> None:
    url = random_url(scheme)
    assert url.scheme == scheme


def test_http_url_defaults_to_http() -> None:
    url = random_http_url()
    assert url.scheme == "http"


@pytest.mark.parametrize("scheme", ("http", "https"))
def test_http_url_sets_scheme(scheme: Literal["http", "https"]) -> None:
    url = random_http_url(scheme)
    assert url.scheme == scheme
