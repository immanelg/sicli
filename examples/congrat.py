from sicli import Sicli

from typing import Literal, Annotated
from pathlib import Path

def congratulate_everyone(
    reason: str,
    language: Literal["en", "fr", "nv"] = "en",
    *,
    output: Annotated[Path, dict(help="File to output congratulations")],
    loud: Annotated[bool, dict(help="IF ENABLED THEM SCREAM")],
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

