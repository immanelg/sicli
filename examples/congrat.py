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
