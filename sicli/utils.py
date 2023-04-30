import inspect
from typing import Any, get_origin, get_args
from collections.abc import Callable


def get_signature(function: Callable) -> inspect.Signature:
    return inspect.signature(function)


def isgeneric(cls: Any) -> bool:
    return hasattr(cls, "__origin__")


def lenient_issubclass(subcls: Any, cls: Any) -> bool:
    return isinstance(subcls, type) and issubclass(subcls, cls)


def unwrap_generic_alias(cls: Any) -> tuple[Any, tuple[Any, ...]]:
    origin, args = get_origin(cls), get_args(cls)
    return origin, args


def snake_to_lower_kebab_case(name: str) -> str:
    return name.lower().strip("_").replace("_", "-")
