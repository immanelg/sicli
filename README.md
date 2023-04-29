# SiCli
## Introduction
`sicli` is a package to build command line utilities in the declarative way, using standard Python type hints. Uses `argparse` under the hood and basically let's you write `argparse` in a better way.

## Quickstart
Let's create a trivial example:
```python
# congrat.py
from sicli import Sicli

from typing import Literal, Annotated
from pathlib import Path

def congratulate_everyone(
    reason: str,
    language: Literal["en", "fr", "nv"] = "en",
    *,
    output: Annotated[Path, dict(help="File to output congratulations")],
    loud: Annotated[bool, dict(help="IF ENABLED THEN SCREAM")],
    names: list[str] = [],
) -> None:
    if language in {"fr", "nv"}:
        print("But I don't speak french... And navajo...")
        return
    for name in names:
        congratulation = f"Happy {reason}, {name}!"
        if loud:
            congratulation = congratulation.upper()
        print(congratulation)
    print("Writing to file", output.resolve())

if __name__ == "__main__":
    cli = Sicli(prog="Congratulator")
    cli(congratulate_everyone)
```

This produces the following output:
```
$ python3 -m congrat --help
usage: Congratulator [-h] [--output OUTPUT] [--loud] [--names [NAMES ...]] reason [{en,fr,nv}]

Built with Sicli™

positional arguments:
  reason
  {en,fr,nv}

options:
  -h, --help            show this help message and exit
  --output OUTPUT, -o OUTPUT
                        File to output congratulations
  --loud, -l            IF ENABLED THEN SCREAM
  --names [NAMES ...], -n [NAMES ...]
```
Let's test it:
```
$ python3 -m congrat 'New Year' en --loud -o ./newyear.txt --names Maria Katherine Julia
HAPPY NEW YEAR, MARIA!
HAPPY NEW YEAR, KATHERINE!
HAPPY NEW YEAR, JULIA!
Writing to file /home/alex/repos/sicli/newyear.txt
```

## Usage
### Arguments vs options
`sicli` interprets regular arguments as positional arguments and keyword-only (after `*`) arguments as options.
### Default values
For both positional and optional arguments, default values in functions are being interpreted as `default=...` argument for `argparse`' `argparse.ArgumentParser.add_argument`. Option `nargs="?"` (zero or one arg) is set for non-list types.
### Types
This is the interesting part. The set of types that `sicli` can interpret is limited to:
- `list[T]` passes `nargs='*'` and `type=T` to `argparse.ArgumentParser.add_argument`.
- `Literal[A, B, ...]` (of the same type)  passes `choices=(A, B, ...)` and `type=type(A)`.
- `Annotated[T, opts]` unwraps `T` (recursively) and merges `opts` to generated kwargs (this is the way to pass arbitrary kwargs to `argparse.ArgumentParser.add_argument`).
- `tuple[...]` is not supported because `argparse` doesn't directly support `nargs` with heterogeneous types. It would require a custom `action`.
- Note that nesting of types is not supported (Like `list[Literal[Annotated[int, {}]]]` won't work). Only `Annotated` can wrap something.
- `bool` is being interpreted as flag (`"store_true"`).
- Any other type supported by `argparse` will be directly passed to `type`.
### `Sicli` object
`sicli.Sicli` wraps `argparse.ArgumentParser`, so you can pass any argument you want as `**kwargs`.
### `Sicli.__call__`
You can pass CLI arguments to it directly instead of parsing `sys.argv`. For example, for testing.
```python
cli(congratulate_everyone, "'New Year' en --loud -o  blah blah blah")
```
## Motivation
For fun.
## Alternatives
[Click](https://click.palletsprojects.com/en): Greatest and feature-rich CLI framework.

[Typer](https://typer.tiangolo.com/): Very cool Click wrapper based on type hints. Pretty similar to `sicli`, but based on Click and doesn't use `Annotated`.

[Plac](https://plac.readthedocs.io/en/latest/): Simple and convenient wrapper for `argparse`. Doesn't use type hints for types. Even simpler, than `sicli`: no `nargs`, for example.
