import random
import string
import uuid
from collections.abc import Callable, Generator, Sequence
from contextlib import ExitStack, contextmanager
from typing import Any
from unittest.mock import patch

from pydantic import AnyUrl, EmailStr, HttpUrl


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=32))


def random_email() -> EmailStr:
    return f"{random_lower_string()}@{random_lower_string()}.com"


def random_url() -> str:
    return AnyUrl(f"http://{random_lower_string()}.com").unicode_string()


def random_http_url() -> str:
    return HttpUrl(f"{random_url()}").unicode_string()


@contextmanager
def patch_password_hashing(*modules: str) -> Generator[None, None, None]:
    """
    Contextmanager to patch ``pwd_context`` in the given modules.
    :param modules: list of modules to patch.
    :return:
    """
    with ExitStack() as stack:
        for module in modules:
            stack.enter_context(
                patch(f"{module}.password_hash.verify", lambda x, y: x == y)
            )
            stack.enter_context(patch(f"{module}.password_hash.hash", lambda x: x))
        yield


type KeyType[O, K] = Callable[[O], K]


def check_lists[O: Any, K: (str, uuid.UUID)](
    actual: Sequence[O],
    expected: Sequence[O],
    key: KeyType[O, K] = lambda o: o.id,
) -> None:
    __tracebackhide__ = True
    assert sorted(actual, key=key) == sorted(expected, key=key)
