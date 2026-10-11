#!/usr/bin/env python3
"""Build a separate bibliography view from BibTeX, never touching publications1.md."""
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
    # Basic common LaTeX accents and commands, without changing the source BibTeX.
    for source, target in [(r'{\\o}', 'ø'), (r'{\\O}', 'Ø'), (r'\\o', 'ø'), (r'{\\ss}', 'ß'), (r'\\&', '&')]:
        value = value.replace(source, target)
    return re.sub(r"\\s+", " ", value).strip()

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
    groups[year if re.fullmatch(r"\\d{4}", year) else "Other"].append(r)

lines = [
    "---", "layout: default", "title: Structured Bibliography",
    "permalink: /bibliography/", "---",
    '<p class="bib-intro">Browse the structured publication records by year. '
    '<a href="/publications1">Original publication list</a> · '
    '<a href="/assets/papers.bib" download>Download BibTeX</a></p>',
    f'<p class="bib-count">{len(records)} records</p>'
]
for year in sorted(groups, key=lambda y: int(y) if y.isdigit() else -1, reverse=True):
    lines.append(f'<h2 class="bib-year">{safe(year)}</h2>')
    lines.append('<div class="bib-group">')
    for r in sorted(groups[year], key=lambda x: clean(x.get("title", "")).lower()):
        title = safe(r.get("title", "(Untitled publication)"))
        authors = safe(r.get("author", r.get("editor", ""))).replace(" and ", " · ")
        venue = safe(r.get("journal", r.get("booktitle", r.get("publisher", r.get("organization", "")))))
        pages = safe(r.get("pages", ""))
        url = link_for(r)
        key = safe(r["ID"])
        kind = safe(r.get("ENTRYTYPE", "publication")).capitalize()
        lines += [f'<article class="bib-entry" id="{key}">',
                  f'<div class="bib-type">{kind}</div>',
                  f'<h3>{title}</h3>']
        if authors: lines.append(f'<p class="bib-authors">{authors}</p>')
        if venue: lines.append(f'<p class="bib-venue">{venue}{(" · pp. " + pages) if pages else ""}</p>')
        if url: lines.append(f'<p class="bib-actions"><a href="{escape(url, quote=True)}">Publisher / DOI ↗</a></p>')
        lines.append('</article>')
    lines.append('</div>')

target = ROOT / "bibliography" / "index.html"
target.parent.mkdir(parents=True, exist_ok=True)
target.write_text("\n".join(lines) + "\n", encoding="utf-8")
assets = ROOT / "assets"
assets.mkdir(exist_ok=True)
(assets / "papers.bib").write_text(raw, encoding="utf-8")
print(f"Built {len(records)} bibliography records across {len(groups)} year groups at /bibliography/")
