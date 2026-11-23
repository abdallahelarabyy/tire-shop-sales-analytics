"""Validate every PBIR JSON file in a .Report folder against Microsoft's published schemas."""
import json
import sys
import urllib.request
from pathlib import Path

from jsonschema import Draft7Validator
from referencing import Registry, Resource

CACHE = Path(__file__).parent / "schemas" / "cache"
CACHE.mkdir(parents=True, exist_ok=True)
PREFIX = "https://developer.microsoft.com/json-schemas/"
RAW = "https://raw.githubusercontent.com/microsoft/json-schemas/main/"


def fetch(uri: str) -> dict:
    path = CACHE / (uri.replace(PREFIX, "").replace("/", "_"))
    if not path.exists():
        with urllib.request.urlopen(uri.replace(PREFIX, RAW), timeout=30) as r:
            path.write_bytes(r.read())
    return json.loads(path.read_text(encoding="utf-8"))


def retrieve(uri: str) -> Resource:
    return Resource.from_contents(fetch(uri))


def main(report_dir: str) -> int:
    registry = Registry(retrieve=retrieve)
    errors = 0
    files = [p for p in Path(report_dir).rglob("*.json") if "StaticResources" not in p.parts]
    for f in files:
        doc = json.loads(f.read_text(encoding="utf-8"))
        uri = doc.get("$schema")
        if not uri:
            continue
        validator = Draft7Validator(fetch(uri), registry=registry)
        for e in validator.iter_errors(doc):
            errors += 1
            print(f"{f.relative_to(report_dir)}: {'/'.join(map(str, e.path))}: {e.message[:200]}")
    print(f"{len(files)} files checked, {errors} schema errors")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main(sys.argv[1]))
