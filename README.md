# Sicli
## Introduction
`sicli` is a package to build command line utilities in a simple, dclarative way, using standard Python type hints, without unecessary complexity of standard `argparse` module. It uses `argparse` under the hood, so there's no external dependencies. Note that if you want to build a very complex CLI, you rather need to use a framework like [Click](https://click.palletsprojects.com/en) or [Typer](https://typer.tiangolo.com/).

## Quickstart
Let's create a trivial example:
```python

from sicli import cli

from typing import Literal, Annotated
from pathlib import Path


@cli(epilog="And that's how you make people happy")
def congratulate(
    reason: str,
    language: Literal["en", "fr"] = "en",
    numbers: Annotated[list[float], {"help": "Throw me some numbers"}] = [],
    *,
    output: Path,
    loud: Annotated[bool, {"help": "SCREAM"}],
    names: list[str] = [],
) -> None:
    """
    This program congratulates everyone if you haven't guessed.
    By the way, this doctring is the help message for the CLI.
    """
    if language == "fr":
        print("But I don't speak french...")
        return
    for name in names:
        if loud:
            print(f"happy {reason}, {name}!!1!".upper())
        else:
            print(f"happy {reason}, {name}.")
    print("Writing to file", output.resolve())
    print(f"Here's the sum of your numbers: {sum(numbers)}")


if __name__ == "__main__":
    congratulate()
```

This produces the following help output:
```
$ python3 -m examples.congrat --help
usage: congrat.py [-h] [--output OUTPUT] [--loud] [--names [NAMES ...]] reason [{en,fr}] [numbers ...]

This program congratulates everyone if you haven't guessed. By the way, this doctring is the help message for the CLI.

positional arguments:
  reason
  {en,fr}
  numbers              Throw me some numbers

options:
  -h, --help           show this help message and exit
  --output OUTPUT
  --loud               SCREAM
  --names [NAMES ...]

And that's how you make people happy
```
Let's now test it:
```
$ python3 -m examples.congrat 'New Year' en 1 2 3 --loud --output ./here.txt --names Elizabeth Maria
HAPPY NEW YEAR, ELIZABETH!!1!
HAPPY NEW YEAR, MARIA!!1!
Writing to file /home/alex/repos/sicli/here.txt
Here's the sum of your numbers: 6.0
```

## Usage
### Creating endpoint
As you can see, you can just wrap your function with `cli` decorator and then call it. It will parse `sys.argv` and call wrapped function with the appropriate arguments.
### Arguments vs options
- Regular arguments are mapped to positional arguments in CLI.
- Keyword-only arguments (after `*`) are mapped to options.
### Default values
Default values for both types of arguments are mapped, as your intuition would suggest, to default arguments in CLI.
Internally, they are passed to  `default` argument in `argparse.ArgumentParser.add_argument` and `nargs="?"` is passed for non-list types.
### Types

#### `Annotated[A, B]`
`Annotated[T, opts]` is the way to pass additional arguments (and override) to `argparse.ArgumentParser.add_argument`. `sicli` unwraps `T`, does whatever would be done with `T`, and merges `opts` to generated kwargs. 

#### `list[T]`
`list[T]` lets you pass multiple arguments. Internally, `sicli` passes `nargs='*'` and `type=T` to `argparse.ArgumentParser.add_argument`. `tuple[...]` is not supported because `argparse` doesn't directly support `nargs` with heterogeneous types. It would require a custom `action`.

#### `Literal[A, B, ...]`
`Literal[A, B, ...]` lets you restrict values. Internally, `sicli` passes `choices=(A, B, ...)` to `argparse.ArgumentParser.add_argument`.

#### `Enum`
Works in the same way as `Literal`.

#### `bool`
- `bool` is being interpreted as flag (`"store_true"`).

#### Other types
Any other primitive type that you would pass to `type` argument in `argparse.ArgumentParser.add_argument` would work. For instance, `int`, `str`, `Path`.
Note that you can override type annotation and even pass an arbitrary converter function to `type` as you would do in `argparse` using `Annotated` metadata:
```python
def example(
    s: Annotated[str, {"type": ascii}],
):
```
That way your editor won't complain about types.

#### Limitations
Note that arbitrary nesting of types is not supported (Like in `list[Annotated[Literal[1, 2, 3], {}]]`). Only `Annotated` can wrap other generic types.

## Requirements
No dependencies are needed, only pure Python ≥ `3.10`.

## Installation
Not available in PyPi for now. Clone the repo and build it yourself.
```
git clone git@github.com:immanelg/sicli.git
```
And then
```
flit build
flit install
```

## Motivation
I needed something simple and convenient. But mainly, it is all for fun.

## Alternatives
[Click](https://click.palletsprojects.com/en): The greatest CLI toolkit. Use it if you want to have a complex CLI.

[Typer](https://typer.tiangolo.com/): Very cool package that wraps Click, based on type hints. Similar to `sicli`.

[Plac](https://plac.readthedocs.io/en/latest/): Simple and convenient wrapper for `argparse`. Doesn't use type hints for types. Even simpler, than `sicli`: no `nargs`, for example.
