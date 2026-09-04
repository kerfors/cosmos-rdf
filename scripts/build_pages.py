"""Build the GitHub Pages site from every release tag.

For each tag vX.Y.Z the deliverables at the repo root of that tag are written to
<site>/vX.Y.Z/: every *.ttl and *.jsonld as committed, plus N-Triples, RDF/XML and
JSON-LD derived from each Turtle graph (the shapes graphs and contexts are copied,
not converted - a shapes graph is served as the Turtle it was generated as). An
index.html per release lists the files with their media types; the root index
lists the releases. This is what https://w3id.org/cdisc/cosmos/ redirects to
(docs/htaccess.txt), so the layout here and the targets there change together.

Requires git and rdflib. Run from repo root: python scripts/build_pages.py site
"""

import html
import re
import subprocess
import sys
from pathlib import Path

from rdflib import Graph

DERIVED = [("nt", "nt", "application/n-triples"), ("rdf", "xml", "application/rdf+xml"), ("jsonld", "json-ld", "application/ld+json")]
MEDIA = {"ttl": "text/turtle", "jsonld": "application/ld+json", "nt": "application/n-triples", "rdf": "application/rdf+xml"}
TAG = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")


def git(*args):
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def page(title, body):
    return (
        "<!doctype html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">"
        f"<title>{html.escape(title)}</title>"
        "<style>body{font-family:system-ui,sans-serif;max-width:56rem;margin:2rem auto;padding:0 1rem;line-height:1.45}"
        "code{font-size:.95em}table{border-collapse:collapse}td,th{text-align:left;padding:.2rem .8rem .2rem 0;vertical-align:top}</style>"
        f"</head><body>{body}</body></html>\n"
    )


site = Path(sys.argv[1])
site.mkdir(parents=True, exist_ok=True)

tags = sorted((t for t in git("tag", "--list").split() if TAG.match(t)),
              key=lambda t: tuple(int(n) for n in t[1:].split(".")))
if not tags:
    raise RuntimeError("no release tags")

releases = []
for tag in tags:
    out = site / tag
    out.mkdir(exist_ok=True)
    root_files = sorted(f for f in git("ls-tree", "--name-only", tag).splitlines() if "/" not in f)
    served = []
    for name in root_files:
        if not (name.endswith(".ttl") or name.endswith(".jsonld")):
            continue
        content = subprocess.run(["git", "show", f"{tag}:{name}"], check=True, capture_output=True).stdout
        (out / name).write_bytes(content)
        served.append(name)
        if name.endswith(".ttl") and ".shapes." not in name:
            graph = Graph().parse(data=content, format="turtle")
            base = name[: -len(".ttl")]
            for ext, fmt, _ in DERIVED:
                derived = out / f"{base}.{ext}"
                derived.write_text(graph.serialize(format=fmt), encoding="utf-8")
                served.append(derived.name)
    rows = "".join(
        f"<tr><td><a href=\"{html.escape(n)}\"><code>{html.escape(n)}</code></a></td>"
        f"<td><code>{MEDIA[n.rsplit('.', 1)[1]]}</code></td>"
        f"<td>{'canonical' if n.endswith('.ttl') or n.endswith('.jsonld') else 'derived from the Turtle at deploy'}</td></tr>"
        for n in sorted(served)
    )
    (out / "index.html").write_text(page(
        f"cosmos-rdf {tag}",
        f"<h1>cosmos-rdf {tag}</h1>"
        "<p>RDF/OWL rendering of CDISC COSMoS and the qualified-BC overlay, at this release. "
        "Dereference target of <code>https://w3id.org/cdisc/cosmos/</code>. "
        "Draft, not a normative CDISC artifact. "
        "<a href=\"https://github.com/kerfors/cosmos-rdf\">Repository</a> &middot; <a href=\"../\">All releases</a></p>"
        f"<table><tr><th>file</th><th>media type</th><th></th></tr>{rows}</table>"
        "<p>Per-IRI HTML descriptions are not rendered yet; every IRI resolves to the graph that describes it.</p>",
    ), encoding="utf-8")
    releases.append((tag, len(served)))
    print(f"{tag}: {len(served)} files")

latest = releases[-1][0]
items = "".join(
    f"<li><a href=\"{t}/\"><code>{t}</code></a> &mdash; {n} files{' (current w3id target)' if t == latest else ''}</li>"
    for t, n in reversed(releases)
)
(site / "index.html").write_text(page(
    "cosmos-rdf releases",
    "<h1>cosmos-rdf</h1>"
    "<p>An RDF/OWL rendering of CDISC COSMoS &mdash; Biomedical Concepts and SDTM Dataset Specializations &mdash; "
    "generated mechanically from the artifacts CDISC publishes, plus an overlay graph of qualified biomedical concepts. "
    "This site serves the deliverables per release for <code>https://w3id.org/cdisc/cosmos/</code>. "
    "Draft, not a normative CDISC artifact. <a href=\"https://github.com/kerfors/cosmos-rdf\">Repository</a></p>"
    f"<h2>Releases</h2><ul>{items}</ul>",
), encoding="utf-8")
(site / ".nojekyll").write_text("", encoding="utf-8")
print(f"site: {len(releases)} releases, latest {latest}")
