from argparse import ArgumentParser
from collections.abc import Iterable, Sequence
from typing import Any, Literal, Annotated, Tuple, Union, List
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
    """Wrapper for parser that can parse function signatures."""

    _parser: ArgumentParser

    def __init__(self, **argument_parser_kwargs: Any) -> None:
        self._parser = ArgumentParser(**(argument_parser_kwargs or {}))

    def _add_function(self, function: AnyCallable, parser) -> None:
        """Parses function signature and adding arguments to parser."""
        for param in get_signature(function).parameters.values():
            is_positional = param.kind == param.POSITIONAL_OR_KEYWORD
            is_option = param.kind == param.KEYWORD_ONLY

            if not is_option and not is_positional:
                # just not touch it
                continue

            type_annotation = param.annotation

            type_annotation, varargs, kwargs = self._unwrap_annotated(type_annotation)

            origin, typeargs = unwrap_generic_alias(type_annotation)

            if origin is Literal:
                kwargs = {"choices": typeargs, "type": type(typeargs[0])} | kwargs

            elif origin is Union:
                # TODO
                raise ValueError("Union types are currently not supported")

            elif lenient_issubclass(origin, (tuple, Tuple)):
                # `nargs` do not support heterogeneous types
                # we can manually implement that but i'm lazy
                raise ValueError("Tuples are currently unsupported, use `list` instead")

            elif lenient_issubclass(origin, (list, List, Sequence, Iterable)):
                kwargs = {"nargs": "*", "type": typeargs[0]} | kwargs
                if isgeneric(typeargs[0]):
                    raise ValueError("Complex generic types are currently unsupported")

            elif origin is not None:
                raise ValueError(f"Unrecognized generic type {origin}")

            elif issubclass(type_annotation, Enum):
                choices = tuple(c for c in type_annotation)
                kwargs = {"choices": choices, "type": type_annotation} | kwargs

            elif issubclass(type_annotation, bool):
                kwargs = {"action": "store_true"} | kwargs

            elif type_annotation is param.empty:
                pass

            else:
                # case when regular param
                kwargs = {"type": type_annotation, "action": "store"} | kwargs

            if param.default != param.empty:
                kwargs = {"default": param.default} | kwargs

                if (
                    kwargs.get("action") == "store_true"
                    and kwargs.get("default") is True
                ):
                    raise ValueError("Flag default value should be False")

            elif is_option and not kwargs.get("action") == "store_true":
                # if we don't have a default value and it is not a flag, require
                # the argument instead of passing None
                # we do it only for options because argparse is raising
                # `'required' is an invalid argument for positionals`
                kwargs = {"required": True} | kwargs

            if (
                kwargs.get("default") is not None
                and kwargs.get("nargs") != "*"
                and not kwargs.get("action") == "store_true"
            ):
                # Always respect the existence of default value
                # (except when flag and when multiple arguments)
                kwargs = {"nargs": "?"} | kwargs

            param_name = param.name

            if not varargs:
                if is_positional:
                    varargs = [snake_to_lower_kebab_case(param_name)]
                else:
                    varargs = ["--" + snake_to_lower_kebab_case(param_name)]

            if is_option:
                kwargs = {"dest": param_name} | kwargs

            parser.add_argument(*varargs, **kwargs)

            parser.description = parser.description or inspect.getdoc(function)

    def _unwrap_annotated(
        self,
        type_annotation: Any,
    ) -> tuple[Any, list[Any], dict[str, Any]]:
        """Unwrap type, help, args and kwargs from `Annotated`."""

        origin, args = unwrap_generic_alias(type_annotation)

        if origin is not Annotated:
            return type_annotation, [], {}

        type_ = args[0]
        varargs = []
        kwargs = {}

        for arg in args:
            if isinstance(arg, str):
                kwargs["help"] = arg
            elif isinstance(arg, list):
                varargs.extend(arg)
            elif isinstance(arg, dict):
                kwargs |= arg

        return type_, varargs, kwargs

    def _add_single_command(self, function: AnyCallable) -> None:
        parser = self._parser
        self._add_function(function, parser)
        parser.set_defaults(__function=function)

    def _add_multiple_commands(self, functions: Iterable[AnyCallable]) -> None:
        subparsers = self._parser.add_subparsers()
        for function in functions:
            parser = subparsers.add_parser(snake_to_lower_kebab_case(function.__name__))
            self._add_function(function, parser)
            parser.set_defaults(__function=function)

    def add_commands(self, functions: AnyCallable | Iterable[AnyCallable]) -> None:
        if isinstance(functions, Iterable):
            self._add_multiple_commands(functions)
        else:
            self._add_single_command(functions)

    def __call__(self, args: list[str] | None = None) -> Any:
        parsed_args = self._parser.parse_args(args)
        kwargs = vars(parsed_args)
        function = kwargs.pop("__function")
        return function(**kwargs)


def run(
    functions: AnyCallable | Iterable[AnyCallable],
    args: list[str] | None = None,
    **argument_parser_kwargs,
) -> None:
    cli = Sicli(**argument_parser_kwargs)
    cli.add_commands(functions)
    return cli(args)
