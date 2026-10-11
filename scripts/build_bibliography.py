#!/usr/bin/env python3
"""Build the main publications view from BibTeX; preserve publications-archive.md."""
from collections import defaultdict
from html import escape
from pathlib import Path
from urllib.parse import quote
import re
import bibtexparser

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "_bibliography" / "papers.bib"
raw = SOURCE.read_text(encoding="utf-8")
parser = bibtexparser.bparser.BibTexParser(common_strings=True, interpolate_strings=False)
records = bibtexparser.loads(raw, parser=parser).entries

if len(records) < 45:
    raise RuntimeError(f"Bibliography parse produced only {len(records)} records (expected at least 45)")
keys = [r["ID"] for r in records]
if len(keys) != len(set(keys)):
    raise RuntimeError("Duplicate BibTeX citation keys")

def clean(value):
    value = str(value or "").replace("\\&", "&").replace("---", "—").replace("--", "–")
    # Decode LaTeX umlauts, including R{\"u}egger, {\"u}, and \"u forms.
    umlaut = {"a": "ä", "o": "ö", "u": "ü", "A": "Ä", "O": "Ö", "U": "Ü"}
    value = re.sub(r'\{\\"([aouAOU])\}', lambda m: umlaut[m.group(1)], value)
    value = re.sub(r'\\"\{([aouAOU])\}', lambda m: umlaut[m.group(1)], value)
    value = re.sub(r'\\"([aouAOU])', lambda m: umlaut[m.group(1)], value)
    for source, target in [(r'{\o}', 'ø'), (r'{\O}', 'Ø'), (r'\o', 'ø'), (r'{\ss}', 'ß'), (r'\ss', 'ß'), (r'\&', '&')]:
        value = value.replace(source, target)
    value = value.replace('{', '').replace('}', '')
    return re.sub(r"\s+", " ", value).strip()

def safe(text):
    return escape(clean(text), quote=True)

def link_for(r):
    doi = clean(r.get("doi", "")).strip()
    url = clean(r.get("url", "")).strip()
    if doi and doi.lower() not in ("none", "n/a", "-"):
        return "https://doi.org/" + quote(doi, safe="/.-_")
    if url.startswith(("https://", "http://")):
        return url
    return ""

groups = defaultdict(list)
for r in records:
    year = clean(r.get("year", "")).strip("{} ")
    groups[year if re.fullmatch(r"\d{4}", year) else "Other"].append(r)

lines = [
    "---", "layout: default", "title: Publications",
    "permalink: /publications1", "---",
    '<div class="scholar-list">',
    '<p class="scholar-intro">Publications by year · '
    '<a href="/publications-archive">Original publication archive</a> · '
    '<a href="/assets/papers.bib" download>Download BibTeX</a></p>',
    f'<p class="scholar-count">{len(records)} publications and contributions</p>'
]
for year in sorted(groups, key=lambda y: int(y) if y.isdigit() else -1, reverse=True):
    lines.append(f'<h2 class="scholar-year">{safe(year)}</h2>')
    lines.append('<div class="scholar-group">')
    for r in sorted(groups[year], key=lambda x: clean(x.get("title", "")).lower()):
        title = safe(r.get("title", "(Untitled publication)"))
        people = clean(r.get("author") or r.get("editor") or "")
        # Preserve bibliographic author order, using familiar full names like Craig Anslow's list.
        formatted = []
        for name in people.split(" and "):
            name = name.strip()
            if "," in name:
                family, given = name.split(",", 1)
                name = (given.strip() + " " + family.strip()).strip()
            if name:
                formatted.append(name)
        authors = escape(", ".join(formatted), quote=True)
        venue = safe(r.get("journal") or r.get("booktitle") or r.get("publisher") or r.get("organization") or "")
        pages = safe(r.get("pages", ""))
        url = link_for(r)
        key = safe(r["ID"])
        citation = f'<span class="scholar-authors">{authors}.</span> ' if authors else ""
        citation += f'<span class="scholar-pubyear">({safe(year)}).</span> '
        title_html = f'<a href="{escape(url, quote=True)}">{title}</a>' if url else title
        citation += f'<span class="scholar-title">{title_html}.</span>'
        if venue:
            suffix = f', pp. {pages}' if pages else ''
            citation += f' <span class="scholar-venue">{venue}{suffix}.</span>'
        lines.append(f'<article class="scholar-entry" id="{key}">')
        lines.append(f'<p class="scholar-citation">{citation}</p>')
        lines.append('</article>')
    lines.append('</div>')
lines.append('</div>')

target = ROOT / "publications1.md"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text("\n".join(lines) + "\n", encoding="utf-8")
# Keep the previously published bibliography address working.
redirect = ROOT / "bibliography" / "index.html"
redirect.parent.mkdir(parents=True, exist_ok=True)
redirect.write_text("""---
layout: default
title: Publications
permalink: /bibliography/
---
<p>The publication list has moved to <a href="/publications1">Publications</a>.</p>
<meta http-equiv="refresh" content="0; url=/publications1">
""", encoding="utf-8")
assets = ROOT / "assets"
assets.mkdir(exist_ok=True)
(assets / "papers.bib").write_text(raw, encoding="utf-8")
print(f"Built {len(records)} bibliography records across {len(groups)} year groups at /publications1")
