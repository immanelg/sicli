# Sicli
## Introduction
`sicli` is a wrapper around standard library module `argparse` that lets you create CLIs in a simple, declarative way.
It parses the signature of your *type-hinted* function and generates CLI from that.

`sicli` is not intended for big and complex applications, so if you need that, you rather need to use a framework like [Click](https://click.palletsprojects.com/en) or [Typer](https://typer.tiangolo.com/).

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

### Creating entry point
The main API of the library is `sicli.run`.
If it's called with a list of functions, they will work as subcommands.
You can pass CLI arguments as the second argument to parse them instead of `sys.argv[1:]`.
Also, you can pass any `**kwargs` to `argparse.ArgumentParser`.

Example:

```python

>>> import sicli
>>> def create_table(*, name: str):
...     print("inited")
... 
>>> def drop_table(*, name: str):
...     print("dropped")
... 
>>> sicli.run([create_table, drop_table], ["drop-table", "--name", "students"], description="cli for your db")
dropped

```

### Arguments vs options
- Regular arguments are mapped to positional arguments in CLI.
- Keyword-only arguments (after `*`) are mapped to options.

### Default values
Default values for both types of arguments are mapped, as your intuition would suggest, to default arguments in CLI. For flags, default value is always `False` and don't have to be set.

### Types

#### `typing.Annotated[T, help, args, kwargs]`
`Annotated` in Python is the way to store metadata inside a valid type.
So, `sicli` uses
- first argument as the type and does whatever would be done with it
- argument of type `str` as help for this argument. 
- argument of type `list` as names for argument. 
- argument of type `dict` to merge it with `*kwargs` for `argparse.ArgumentParser.add_argument` (see `argparse` docs).

Example:
```python

>>> import sicli
>>> from typing import Annotated as Ann
>>> def divide(
...     *,
...     numbers: Ann[
...         list[int],
...         "Numbers to divide",
...         ["+n", "+numbers"],
...         {"nargs": 2},
...     ],
... ):
...     print(numbers[0] / numbers[1])
... 
>>> sicli.run(divide, ["+numbers", "1", "2"], prefix_chars="-+")
0.5

```

#### `list[T], typing.List[T], typing.Sequence[T], typing.Iterable[T]`
As you saw, `list[T]` lets you pass multiple arguments. `tuple[...]` (for heterogeneous types) is not currently not supported.

#### `typing.Literal`
`Literal[A, B, ...]` (of the same type) lets you restrict values.

#### `enum.Enum`
It is recommended to use `Literal` instead, but `enum.Enum` can work similarly. To use it, you need to create `__str__` method like that:
```python
class Color(Enum):
    red = "r"
    black = "b"

    def __str__(self) -> str:
        return self.value
```

#### `bool`
`bool` is interpreted as flag. Its default value is always `False` and shouldn't be set.

#### Other types
Any other primitive type that you would pass to `type` argument in `argparse.ArgumentParser.add_argument` would work. For instance, `int`, `str`, `Path`.

#### Overriding types
You can use `dict` in `Annotated` to override type for `argparse.ArgumentParser.add_argument`:
```python
def example(
    s: Annotated[str, {"type": ascii}],
):
```
You could've used `ascii` directly as type annotation here if you don't care that your type checker will complain.

#### Limitations
Note that arbitrary nesting of types is not supported (Like in `list[Annotated[Literal[1, 2, 3], {}]]`). Only `Annotated` can wrap other generic types.

## Requirements
No dependencies are needed, only pure Python ≥ `3.10`.

## Installation
Install from PyPI:
```
pip install sicli-cli
```

## Motivation
For fun.

## Alternatives
[Click](https://click.palletsprojects.com/en): The greatest CLI toolkit. Use it if you want to have a complex CLI.

[Typer](https://typer.tiangolo.com/): Cool Click wrapper, similar to `sicli`.

[Plac](https://plac.readthedocs.io/en/latest/): Simple wrapper for `argparse`.
