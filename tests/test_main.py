from collections.abc import Iterable, Sequence
from typing import Annotated, List, Literal
from sicli import run
import pytest


def test_basic():
    def f(x: str):
        return x

    assert run(f, ["a"]) == "a"

    with pytest.raises(SystemExit):
        run(f, ["1", "2", "3"])


def test_argument_with_defaults():
    def f(x: int, y: int = 1):
        return x, y

    assert run(f, ["100"]) == (100, 1)
    assert run(f, ["100", "200"]) == (100, 200)


def test_option_with_defaults():
    def f(*, x: int = 1, y: int = 2):
        return x, y

    assert run(f, ["--x", "100"]) == (100, 2)
    assert run(f, ["--x", "100", "--y", "200"]) == (100, 200)


def test_flag():
    def f(x: int, *, y: bool):
        return x, y

    assert run(f, ["12", "--y"]) == (12, True)
    assert run(f, ["12"]) == (12, False)


@pytest.mark.parametrize("seq", [list, Iterable, List, Sequence])
def test_list(seq):
    def f(xs: seq[str], *, ys: seq[int]):
        return xs, ys

    assert run(f, ["a", "b", "--ys", "100", "200"]) == (["a", "b"], [100, 200])
    assert run(f, ["a", "b", "--ys"]) == (["a", "b"], [])


def test_list_default_values():
    def f(xs: list[str] = ["a", "b"], *, ys: list[int] = [3, 4]):
        return xs, ys

    assert run(f, ["--ys", "100", "200"]) == (["a", "b"], [100, 200])
    assert run(f, ["q", "w"]) == (["q", "w"], [3, 4])
    assert run(f, ["q", "w", "--ys", "100", "200"]) == (["q", "w"], [100, 200])


def test_literal():
    def f(x: Literal[1, 2], *, y: Literal[3, 4]):
        return x, y

    assert run(f, ["1", "--y", "3"]) == (1, 3)

    with pytest.raises(SystemExit):
        run(f, ["10", "40"])


def test_enum():
    from enum import Enum

    class Color(Enum):
        red = "r"
        black = "b"

        def __str__(self) -> str:
            return self.value

    def f(c: Color = Color.red):
        return c

    assert run(f, ["r"]) == Color.red

    with pytest.raises(SystemExit):
        run(f, ["white"])


def test_bad_type():
    def f(*, x: int = 1):
        return x

    with pytest.raises(SystemExit):
        assert run(f, ["--x", "NaN"])


def test_annotated_wrapped_type():
    def f(
        x: Annotated[int, "help for x"],
        *,
        y: Annotated[Literal[3, 4], "help for y", {}] = 3,
    ):
        return x, y

    assert run(f, ["1", "--y", "4"]) == (1, 4)


def test_annotated_name_override():
    def f(*, x: Annotated[int, ["-n", "--number"]]):
        return x

    assert run(f, ["-n", "34"]) == 34
    assert run(f, ["--number", "34"]) == 34


def test_subcommands():
    def sub_1(*, x: int):
        return x

    def sub_2(*, y: int):
        return y

    assert run([sub_1, sub_2], ["sub-1", "--x", "1"]) == 1
    assert run([sub_1, sub_2], ["sub-2", "--y", "2"]) == 2
