#!/usr/bin/env python3
"""Portable CWF entrypoint; no installation needed to run tests or plan deployment."""
import sys
sys.dont_write_bytecode = True
from cwf.cli import main
if __name__ == "__main__":
    raise SystemExit(main())
