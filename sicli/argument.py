from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class Arg:
    help: str | None = None
    type: Any = None
    nargs: int | Literal["+", "?", "*"] | None = None
