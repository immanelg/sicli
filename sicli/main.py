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

    def __init__(self, **argument_parser_kwargs: Any) -> None:
        self._parser = ArgumentParser(**(argument_parser_kwargs or {}))
        self._function = None

    def _add_function(self, function: AnyCallable, parser: ArgumentParser) -> None:
        for param in get_signature(function).parameters.values():
            kwargs = self._parse_parameter(param)

            names = [snake_to_lower_kebab_case(param.name)]

            # If argument is keyword-only, it is an option
            if param.kind == param.KEYWORD_ONLY:
                names = ["--" + name for name in names]

            parser.add_argument(*names, **kwargs)

            parser.description = parser.description or inspect.getdoc(function)

    def _parse_parameter(self, param: inspect.Parameter) -> dict[str, Any]:
        kwargs = {}

        type_annotation = param.annotation

        type_annotation, kwargs = self._unwrap_annotated(type_annotation, kwargs)

        origin, args = unwrap_generic_alias(type_annotation)

        if origin is Literal:
            # case when 'choices'
            kwargs = {"choices": args, "type": type(args[0])} | kwargs

        elif origin is Union:
            # unions are obviously not supported by argparse
            raise ValueError("Union types are unsupported")

        # allow only explicit type parameters on generic lists/tuples, so use origin
        elif lenient_issubclass(origin, list):
            # TODO handle Sequence, Iterable, ...
            kwargs = {"nargs": "*", "type": args[0]} | kwargs
            if isgeneric(args[0]):
                raise ValueError("Nested generics for `list` are unsupported")

        elif lenient_issubclass(origin, tuple):
            # `nargs` do not support heterogeneous types
            raise ValueError("Tuples are unsupported, use `list` instead")

        elif origin is not None:
            # Unsupported generic alias
            raise ValueError(f"Unrecognized generic type {origin}")

        elif issubclass(type_annotation, Enum):
            choices = tuple(c for c in type_annotation)
            kwargs = {"choices": choices, "type": type_annotation} | kwargs

        elif issubclass(type_annotation, bool):
            # case when boolean flag
            kwargs = {"action": "store_true"} | kwargs

        elif type_annotation is inspect._empty:
            # no type is provided
            pass

        else:
            # case when regular param
            kwargs = {"type": type_annotation, "action": "store"} | kwargs


        if param.default != inspect._empty:
            kwargs = {"default": param.default} | kwargs
        elif param.kind == param.KEYWORD_ONLY and not kwargs.get("action") == "store_true":
            # if we don't have a default value and it is not a flag, require
            # the argument instead of passing None
            # we do it only for options because argparse is raising
            # `'required' is an invalid argument for positionals`
            kwargs = {"required": True} | kwargs

        if kwargs.get("default") is not None and kwargs.get("nargs") != "*":
            # Always respect the existence of default value
            kwargs = {"nargs": "?"} | kwargs

        return kwargs

    def _unwrap_annotated(
        self, type_annotation: Any, kwargs: dict[str, Any]
    ) -> tuple[Any, dict[str, Any]]:
        origin, args = unwrap_generic_alias(type_annotation)

        if origin is not Annotated:
            return type_annotation, kwargs

        for arg in args:
            if isinstance(arg, dict):
                # kwargs for add_argument
                kwargs |= arg
            elif isinstance(arg, str):
                # help string
                kwargs["help"] = arg

        # return actual type
        return args[0], kwargs

    def add_command(self, function: AnyCallable) -> None:
        self._set_main(function)
        parser = self._parser
        self._add_function(function, parser)

    def _set_main(self, function: AnyCallable) -> None:
        assert self._function is None, "Can only have one function per object"
        self._function = function

    def __call__(self, args: list[str] | None = None) -> Any:
        parsed_args = self._parser.parse_args(args)
        kwargs = vars(parsed_args)
        assert self._function is not None, "Function to call is not provided"
        return self._function(**kwargs)


def run(function: AnyCallable, args: list[str] | None = None,  **argument_parser_kwargs) -> None:
    cli = Sicli(**argument_parser_kwargs)
    cli.add_command(function)
    return cli(args)
