import sicli

from typing import Literal
from typing import Annotated as Ann
from pathlib import Path


def congratulate(
    # positional arguments go here
    reason: str,
    gift: Ann[str, "What to give them"],  # help message
    language: Literal["en", "fr"] = "en",  # choice of values
    # options go here
    *,
    output: Path = Path("./out.txt"),
    loud: Ann[bool, "IF ENABLED THEN SCREAM"],  # this is a flag
    names: list[str] = ["Maria"],
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
