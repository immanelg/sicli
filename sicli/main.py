from argparse import ArgumentParser
from collections.abc import Callable
from typing import Any, Literal, get_args, Annotated, Union
from enum import Enum
import inspect
from .utils import (
    isgeneric,
    unwrap_generic_alias,
    get_signature,
    snake_to_lower_kebab_case,
    lenient_issubclass,
)
from sicli.types import AnyCallable


class Sicli:
    _function: AnyCallable | None
    _parser: ArgumentParser

    def __init__(self, **parser_args: Any) -> None:
        self._parser = ArgumentParser(**(parser_args or {}))
        self._function = None

    def _add_function(self, function: AnyCallable, parser: ArgumentParser) -> None:
        for param in get_signature(function).parameters.values():
            kwargs = self._parse_parameter(param)

            names = [snake_to_lower_kebab_case(param.name)]

            # if param.kind == param.POSITIONAL_OR_KEYWORD:
            #     parser.add_argument(*names, **kwargs)

            # If argument is keyword-only, it is an option
            if param.kind == param.KEYWORD_ONLY:
                names = ["--" + name for name in names]

            parser.add_argument(*names, **kwargs)

            parser.description = parser.description or inspect.getdoc(function)

    def _parse_parameter(self, param: inspect.Parameter) -> dict[str, Any]:
        kwargs = {}

        type_annotation = param.annotation

        if param.default != inspect._empty:
            kwargs = {"default": param.default} | kwargs

        type_annotation, kwargs = self._unwrap_annotated(type_annotation, kwargs)

        origin, args = unwrap_generic_alias(type_annotation)

        if origin is Literal:
            # case when 'choices'
            kwargs = {"choices": get_args(type_annotation)} | kwargs

        elif origin is Union:
            # unions are obviously not supported by argparse
            raise RuntimeError("Union types are unsupported")

        # allow only explicit type parameters on generic lists/tuples, so use origin
        elif lenient_issubclass(origin, list):
            kwargs = {"nargs": "*", "type": args[0]} | kwargs
            if isgeneric(args[0]):
                raise RuntimeError("Nested generics for `list` are unsupported")

        elif lenient_issubclass(origin, tuple):
            # `nargs` do not support heterogeneous types
            raise RuntimeError("Tuples are unsupported, use `list` instead")

        elif issubclass(type_annotation, Enum):
            choices = tuple(c.value for c in type_annotation)
            kwargs = {"choices": choices} | kwargs

        elif issubclass(type_annotation, bool):
            # case when boolean flag
            kwargs = {"action": "store_true"} | kwargs

        else:
            # case when regular param
            kwargs = {"type": type_annotation, "action": "store"} | kwargs

        if kwargs.get("default") is not None and kwargs.get("nargs") != "*":
            # Always respect the existence of default value
            kwargs = {"nargs": "?"} | kwargs

        return kwargs

    def _unwrap_annotated(
        self, type_annotation: Any, kwargs: dict[str, Any]
    ) -> tuple[Any, dict[str, Any]]:
        origin, args = unwrap_generic_alias(type_annotation)
        if origin is Annotated:
            # add metadata
            kwargs |= args[1]
            return args[0], kwargs
        return type_annotation, kwargs

    def add_command(self, function: AnyCallable) -> None:
        self._set_main(function)
        parser = self._parser
        self._add_function(function, parser)

    def _set_main(self, function: AnyCallable) -> None:
        assert self._function is None, "Can only have one function per object"
        self._function = function

    def __call__(self, args: list[str] | None = None) -> None:
        parsed_args = self._parser.parse_args(args)
        kwargs = vars(parsed_args)
        assert self._function is not None, "Function to call is not provided"
        self._function(**kwargs)


def cli(**kwargs: Any) -> Callable[[AnyCallable], Sicli]:
    def wrapper(function: AnyCallable) -> Sicli:
        sicli_object = Sicli(**kwargs)
        sicli_object.add_command(function)
        return sicli_object

    return wrapper


