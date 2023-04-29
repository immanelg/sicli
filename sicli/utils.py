import inspect
from typing import Any, get_origin, get_args
from collections.abc import Callable


def get_signature(function: Callable) -> inspect.Signature:
    return inspect.signature(function)


def isgeneric(cls: Any) -> bool:
    return hasattr(cls, "__origin__")


def unwrap_generic_alias(cls: Any) -> tuple[Any, tuple[Any, ...]]:
    if not isgeneric(cls):
        raise ValueError
    origin, args = get_origin(cls), get_args(cls)
    return origin, args


def snake_to_kebab_case(name: str) -> str:
    return name.strip("_").replace("_", "-")
