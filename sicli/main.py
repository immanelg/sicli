from argparse import ArgumentParser
from collections.abc import Callable
from typing import Any, Literal, get_args, Annotated
import inspect
from .utils import isgeneric, unwrap_generic_alias, get_signature, snake_to_kebab_case


class Sicli:
    main: Callable[..., Any]
    parser: ArgumentParser

    def __init__(self, **parser_args: Any) -> None:
        self.parser = ArgumentParser(
            **{"description": "Built with Sicli™"} | (parser_args or {})
        )

    def _parse_generic_aliases(
        self, type_annotation: Any, kwargs: dict[str, Any]
    ) -> tuple[Any, dict[str, Any]]:
        if not isgeneric(type_annotation):
            return type_annotation, kwargs

        origin, args = unwrap_generic_alias(type_annotation)

        if origin is Annotated:
            # swallow metadata and handle what is wrapped inside
            kwargs |= args[1]
            return self._parse_generic_aliases(args[0], kwargs)

        elif origin is Literal:
            # case when 'choices'
            kwargs["type"] = type(args[0])
            kwargs["choices"] = get_args(type_annotation)
            # dirty hack
            return type(args[0]), kwargs

        elif issubclass(origin, list):
            # case when sequence of values
            kwargs["nargs"] = "*"
            return args[0], kwargs
        else:
            raise RuntimeError(
                f"Unrecognized generic type: origin={origin}, args={args}"
            )

    def _parse_parameter(self, param: inspect.Parameter) -> dict[str, Any]:
        kwargs = {}

        type_annotation = param.annotation

        if param.default != inspect._empty:
            kwargs["default"] = param.default

        if isgeneric(type_annotation):
            # unwrap generics
            type_annotation, kwargs = self._parse_generic_aliases(
                type_annotation, kwargs
            )

        if issubclass(type_annotation, bool):
            # case when boolean flag
            kwargs = {"action": "store_true"} | kwargs
            # kwargs["action"] = "store_true"

        else:
            # case when regular param
            kwargs = {"type": type_annotation, "action": "store"} | kwargs

        if kwargs.get("default") is not None and kwargs.get("nargs") != "*":
            # Always respect the existence of default value
            kwargs = {"nargs": "?"} | kwargs

        return kwargs

    def parse_function(self, function: Callable) -> None:
        for param in get_signature(function).parameters.values():
            name = snake_to_kebab_case(param.name)
            kwargs = self._parse_parameter(param)

            if param.kind == param.POSITIONAL_OR_KEYWORD:
                self.parser.add_argument(name, **kwargs)

            elif param.kind == param.KEYWORD_ONLY:
                self.parser.add_argument("--" + name, "-" + name[0], **kwargs)

        self.main = function

    def __call__(self, fn: Callable[..., Any], args: str | None = None) -> None:
        self.parse_function(fn)
        self.main(
            **vars(self.parser.parse_args(args.split() if args is not None else None))
        )
