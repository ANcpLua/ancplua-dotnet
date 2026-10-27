#!/usr/bin/env python3
"""One-shot portal health assessment. Never starts a background monitor."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

spec = importlib.util.spec_from_file_location("workflow_core", Path(__file__).with_name("workflow_core.py"))
core = importlib.util.module_from_spec(spec)
spec.loader.exec_module(core)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    try:
        result = core.health(json.loads(parser.parse_args().snapshot.read_text()))
        print(json.dumps(result, indent=2))
        sys.exit(0 if result["status"] == "Healthy" else 2 if result["status"] == "Unknown" else 1)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print(json.dumps({"status": "Input error", "message": str(exc)}), file=sys.stderr)
        sys.exit(2)

