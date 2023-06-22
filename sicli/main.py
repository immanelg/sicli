import sys
from argparse import ArgumentParser
from collections.abc import Iterable, Sequence
from typing import Any, Literal, Annotated, Tuple, Union, List
from enum import Enum
from dataclasses import asdict
import inspect
from sicli.utils import (
    isgeneric,
    unwrap_generic_alias,
    get_signature,
    snake_to_lower_kebab_case,
    lenient_issubclass,
)
from sicli.types import AnyCallable
from sicli.exceptions import SicliException
from sicli.argument import Arg


class Sicli:
    """Wrapper for parser that can parse function signatures."""

    _parser: ArgumentParser

    def __init__(self, **argument_parser_kwargs: Any) -> None:
        self._parser = ArgumentParser(**(argument_parser_kwargs or {}))

    def _consume_function(self, function: AnyCallable, parser) -> None:
        """Parses function signature and adding arguments to parser."""
        for param in get_signature(function).parameters.values():
            is_positional = param.kind == param.POSITIONAL_OR_KEYWORD
            is_option = param.kind == param.KEYWORD_ONLY

            if not is_option and not is_positional:
                raise SicliException("Function arguments can only be regular (for positional CLI args) or keyword-only (for CLI options)")

            type_annotation = param.annotation

            type_annotation, varargs, kwargs = self._unwrap_annotated(type_annotation)

            origin, typeargs = unwrap_generic_alias(type_annotation)

            if origin is Literal:
                kwargs = {"choices": typeargs, "type": type(typeargs[0])} | kwargs

            elif origin is Union:
                raise SicliException("Union types are currently not supported")

            elif lenient_issubclass(origin, (tuple, Tuple)):
                # `nargs` do not support heterogeneous types
                # we can manually implement that but it is out of scope to make custom validation
                raise SicliException("Tuples are currently unsupported, use `list` or similar homogeneous collections instead")

            elif lenient_issubclass(origin, (list, List, Sequence, Iterable)):
                kwargs = {"nargs": "*", "type": typeargs[0]} | kwargs
                if isgeneric(typeargs[0]):
                    raise SicliException("Nested generic types are currently unsupported")

            elif origin is not None:
                raise SicliException(f"Unsupported generic type {origin}")

            elif issubclass(type_annotation, Enum):
                choices = tuple(c for c in type_annotation)
                kwargs = {"choices": choices, "type": type_annotation} | kwargs

            elif issubclass(type_annotation, bool):
                kwargs = {"action": "store_true"} | kwargs

            elif type_annotation is param.empty:
                raise SicliException("All parameters should have type annotations")

            else:
                # case when regular param
                kwargs = {"type": type_annotation, "action": "store"} | kwargs

            if param.default != param.empty:
                kwargs = {"default": param.default} | kwargs

                if (
                    kwargs.get("action") == "store_true"
                    and kwargs.get("default") is True
                ):
                    raise SicliException("Flag default value should be False")

            elif is_option and not kwargs.get("action") == "store_true":
                # if we don't have a default value and it is not a flag, require
                # the argument instead of passing None
                # we do it only for options because argparse is raising
                # `'required' is an invalid argument for positionals`
                kwargs = {"required": True} | kwargs

            if (
                kwargs.get("default") is not None
                and kwargs.get("nargs") != "*"
                and kwargs.get("action") != "store_true"
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

        args = list(args)
        type_ = args.pop(0)
        varargs = []
        kwargs = {}

        for arg in args:
            if isinstance(arg, str):
                kwargs["help"] = arg
            elif isinstance(arg, list):
                varargs.extend(arg)
            elif isinstance(arg, Arg):
                override_kwargs = {k: v for (k, v) in asdict(arg).items() if v is not None}
                kwargs |= override_kwargs
            else:
                raise SicliException(
                    f"`Annotated` arguments after the first one must be values of"
                    "type `str`, `list`, or `sicli.Arg`, got {arg} instead"
                )

        return type_, varargs, kwargs

    def _add_single_command(self, function: AnyCallable) -> None:
        parser = self._parser
        self._consume_function(function, parser)
        parser.set_defaults(__sicli_function=function)

    def _add_multiple_commands(self, functions: Iterable[AnyCallable]) -> None:
        subparsers = self._parser.add_subparsers()
        for function in functions:
            parser = subparsers.add_parser(
                snake_to_lower_kebab_case(function.__name__),
                help=inspect.getdoc(function) or None,
            )
            self._consume_function(function, parser)
            parser.set_defaults(__sicli_function=function)

    def add_commands(self, functions: AnyCallable | Iterable[AnyCallable]) -> None:
        if isinstance(functions, Iterable):
            self._add_multiple_commands(functions)
        else:
            self._add_single_command(functions)

    def __call__(self, args: list[str] | None = None) -> Any:
        parsed_args = self._parser.parse_args(args)
        kwargs = vars(parsed_args)
        function: AnyCallable | None = kwargs.pop("__sicli_function", None)
        if function is None:
            self._parser.print_help()
            sys.exit()
        return function(**kwargs)


def run(
    functions: AnyCallable | Iterable[AnyCallable],
    args: list[str] | None = None,
    **argument_parser_kwargs,
) -> None:
    cli = Sicli(**argument_parser_kwargs)
    cli.add_commands(functions)
    return cli(args)
