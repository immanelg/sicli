# Sicli
## Introduction
`sicli` is a package to build command line utilities in a simple, dclarative way, using standard Python type hints, without unecessary complexity of standard `argparse` module. It uses `argparse` under the hood, so there's no external dependencies. Note that if you want to build a very complex CLI, you rather need to use a framework like [Click](https://click.palletsprojects.com/en) or [Typer](https://typer.tiangolo.com/).

## Quickstart
Let's create a simple example:
```python
import sicli

from typing import Literal
from typing import Annotated as Ann
from pathlib import Path


def congratulate(
    # positional arguments go here
    reason: str,
    gift: Ann[str, "What to give them"], # help message
    language: Literal["en", "fr"] = "en", # choice of values 

    # options go here
    *,
    output: Path = Path("./out.txt"),
    loud: Ann[bool, "IF ENABLED THEN SCREAM"], # flag
    names: list[str] = ["Maria"], # multiple arguments
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
        print(f"Here's your {gift}")
    print("Writing to file", output.resolve())


if __name__ == "__main__":
    sicli.run(congratulate)
```

This produces the following output for `--help`:
```
$ python3 -m examples.congrat --help
usage: congrat.py [-h] [--output [OUTPUT]] [--loud] [--names [NAMES ...]] reason gift [{en,fr}]

This program congratulates everyone if you haven't guessed. By the way, this doctring is the help message for the CLI.

positional arguments:
  reason
  gift                 What to give them
  {en,fr}

options:
  -h, --help           show this help message and exit
  --output [OUTPUT]
  --loud               IF ENABLED THEN SCREAM
  --names [NAMES ...]
```

Let's now test out CLI:
```
$ python3 -m examples.congrat Christmas chocolate en --loud --output ./xm.txt --names Elizabath Maria
HAPPY CHRISTMAS, ELIZABATH!!1!
Here's your chocolate
HAPPY CHRISTMAS, MARIA!!1!
Here's your chocolate
Writing to file /home/alex/repos/sicli/xm.txt
```

## Usage

### Creating endpoint
You simply call `sicli.run` on your function and it will parse its signature, parse `sys.argv` and call the function with appropriate arguments.

### Arguments vs options
- Regular arguments are mapped to positional arguments in CLI.
- Keyword-only arguments (after `*`) are mapped to options.

### Default values
Default values for both types of arguments are mapped, as your intuition would suggest, to default arguments in CLI.
Internally, they are passed to  `default` argument in `argparse.ArgumentParser.add_argument` and `nargs="?"` is passed for non-list types.

### Types

#### `Annotated[T, help, opts]`
`Annotated` in Python is the way to store metadata inside a valid type. So, `sicli` interprets first argument as the type and does whatever would be done with it, interprets `str` argument as help for this argument, and `dict` as the kwargs for `argparse.ArgumentParser.add_argument`.

#### `list[T]`
`list[T]` lets you pass multiple arguments. Internally, `sicli` passes `nargs='*'` and `type=T` to `argparse.ArgumentParser.add_argument`. `tuple[...]` is not supported because `argparse` doesn't directly support `nargs` with heterogeneous types. It would require a custom `action`.

#### `Literal[A, B, ...]`
`Literal[A, B, ...]` lets you restrict values. Internally, `sicli` passes `choices=(A, B, ...)` to `argparse.ArgumentParser.add_argument`.

#### `Enum`
Works in the same way as `Literal`, and passes `Enum` class to `type`.

#### `bool`
`bool` is being interpreted as flag (`"store_true"`).

#### Other types
Any other primitive type that you would pass to `type` argument in `argparse.ArgumentParser.add_argument` would work. For instance, `int`, `str`, `Path`.

#### Overriding types
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
For fun.

## Alternatives
[Click](https://click.palletsprojects.com/en): The greatest CLI toolkit. Use it if you want to have a complex CLI.

[Typer](https://typer.tiangolo.com/): Very cool package that wraps Click, based on type hints. Similar to `sicli`.

[Plac](https://plac.readthedocs.io/en/latest/): Simple and convenient wrapper for `argparse`. Doesn't use type hints for types. Even simpler, than `sicli`: no `nargs`, for example.
