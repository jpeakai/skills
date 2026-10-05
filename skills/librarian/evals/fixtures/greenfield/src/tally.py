"""Count words in a text file."""

import sys
from pathlib import Path


def count_words(path: Path) -> int:
    return len(path.read_text(encoding="utf-8").split())


def main() -> None:
    print(count_words(Path(sys.argv[1])))
