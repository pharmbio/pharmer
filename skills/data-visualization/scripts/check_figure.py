#!/usr/bin/env python
"""Audit exported figure files against a journal spec.
Usage: python check_figure.py fig1.pdf fig1.tiff --journal nature
Exit code 0 = all pass, 1 = issues found."""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pubfig as pf

ap = argparse.ArgumentParser()
ap.add_argument("files", nargs="*")
ap.add_argument("--journal", default="generic")
ap.add_argument("--list", action="store_true", help="list known journals and exit")
a = ap.parse_args()
if a.list:
    pf.list_journals(); sys.exit(0)
bad = 0
for f in a.files:
    bad += len(pf.audit_file(f, a.journal))
sys.exit(1 if bad else 0)
