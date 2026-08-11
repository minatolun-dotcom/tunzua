#!/usr/bin/env python3
"""Shared scaffolding for the standalone generator test scripts.

Every scripts/test-*.py used to re-declare the repo path, a load_generator()
import helper and a check()/fails verdict pattern. This module centralises that
tiny, dependency-free core so all suites stay consistent (stdlib only, matching
the generator's own conventions).

The `fails` list is process-global: each test script runs in its own Python
process, so failures can never leak from one suite into another.
"""

import importlib.util
import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

fails = []


def load_generator():
    """Import scripts/generate-digest.py as a module (never executes it)."""
    spec = importlib.util.spec_from_file_location(
        "generate_digest", os.path.join(REPO, "scripts", "generate-digest.py")
    )
    gd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gd)
    return gd


def check(name, cond, extra=""):
    """Record and print one check; failures are collected in the shared list."""
    print(("ok  : " if cond else "FAIL: ") + name + ((" | " + extra) if extra else ""))
    if not cond:
        fails.append(name)


def verdict(suite_name, fail_list=None):
    """Print the suite verdict and return the process exit code."""
    f = fail_list if fail_list is not None else fails
    if f:
        print(f"== {suite_name} FAILED ==")
        for item in f:
            print("  FAIL: " + item)
        return 1
    print(f"== {suite_name} PASSED ==")
    return 0
