#!/usr/bin/env python3
"""
ZOLA TOOLKIT — read-only catalog of available Claude Code tools.

NOT the self-improving loop. zola_skills.py only stores a skill once it's been
BORN from a real, rated outcome (see zola_learn.py). This module is the other
half: a static list of what's currently INSTALLED and available to use, so a
session can ask "what tools exist for this shape/theory" before anything has
been proven. A tool graduates from here into zola_skills.jsonl only once it's
actually used and rated. Never write to zola_skills.jsonl from this file.

Store (read-only): ../zola-skillset.local.json

  python3 zola_toolkit.py list                 # every department + skill
  python3 zola_toolkit.py shape <white|blue|black>   # departments matching a shape
  python3 zola_toolkit.py theory "<keyword>"   # departments matching a theory keyword
"""
import json, os, sys

CATALOG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "zola-skillset.local.json")

def _load():
    try:
        with open(CATALOG) as f: return json.load(f)
    except Exception: return {"departments": []}

def list_all():
    return _load().get("departments", [])

def by_shape(shape):
    shape = shape.lower()
    return [d for d in list_all() if shape in [s.lower() for s in d.get("shape", [])]]

def by_theory(keyword):
    keyword = keyword.lower()
    return [d for d in list_all() if keyword in d.get("theory", "").lower()]

if __name__ == "__main__":
    a = sys.argv[1:]
    if not a: print(__doc__); sys.exit(0)
    if a[0] == "list":
        print(json.dumps(list_all(), indent=1))
    elif a[0] == "shape" and len(a) > 1:
        print(json.dumps(by_shape(a[1]), indent=1))
    elif a[0] == "theory" and len(a) > 1:
        print(json.dumps(by_theory(" ".join(a[1:])), indent=1))
    else:
        print(__doc__)
