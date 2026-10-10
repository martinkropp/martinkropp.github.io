#!/usr/bin/env python3
"""Generate the Publications page from _bibliography/papers.bib.

No third-party dependencies. Archive BibTeX notes are the display citations.
"""
from collections import defaultdict
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent.parent
source = (ROOT / "_bibliography" / "papers.bib").read_text(encoding="utf-8")
records = []
for match in re.finditer(r"(?ms)^@\w+\{([^,]+),\s*\n(.*?)^\}\s*$", source):
    key, body = match.groups()
    fields = dict(re.findall(r"(?m)^\s*(\w+)\s*=\s*\{(.*)\},?\s*$", body))
    # Reverse simple BibTeX escapes written by the migration converter.
    note = fields.get("note", "").replace(r"\{", "{").replace(r"\}", "}").replace(r"\\", "\")
    year = fields.get("year", "Undated")
    records.append((year, key, note))

groups = defaultdict(list)
for year, key, note in records:
    groups[year].append((key, note))

out = ["---", "title: Publications", "permalink: /publications1", "---", "", "## Publications", "",
       f"{len(records)} publications and contributions.", "",
       "[Download all citations in BibTeX](/_bibliography/papers.bib)", ""]
for year in sorted(groups, key=lambda y: int(y) if y.isdigit() else 0, reverse=True):
    out += [f"## {year}", ""]
    for key, note in groups[year]:
        out += [f'<span id="{key}"></span>', f"- {note}", ""]
(ROOT / "publications1.md").write_text("\n".join(out) + "\n", encoding="utf-8")
print(f"Generated {len(records)} citations over {len(groups)} year groups")
