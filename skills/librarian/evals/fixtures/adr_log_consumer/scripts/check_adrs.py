"""CI gate: every decision record under adrs/ is a YAML file with an id and a status."""

import sys
from pathlib import Path

import yaml

records = sorted(Path("adrs").glob("*.yml"))
if not records:
    sys.exit("no adrs/*.yml records found")
for path in records:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not data.get("id") or not data.get("status"):
        sys.exit(f"{path}: missing id or status")
