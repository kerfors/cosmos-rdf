"""Build the GitHub Pages site from every release tag.

For each tag vX.Y.Z the deliverables at the repo root of that tag are written to
<site>/vX.Y.Z/: every *.ttl and *.jsonld as committed, plus N-Triples, RDF/XML and
JSON-LD derived from each Turtle graph (the shapes graphs and contexts are copied,
not converted - a shapes graph is served as the Turtle it was generated as). An
index.html per release lists the files with their media types; the root index
lists the releases. This is what https://w3id.org/cdisc/cosmos/ redirects to
(docs/htaccess.txt), so the layout here and the targets there change together.

With --widoco <jar>, every ontology at the tag - a root *.ttl that is neither a
shapes nor an instances graph - is also documented with WIDOCO into
<site>/vX.Y.Z/doc-<name>/, and the release index links it. owl:imports are
rewritten to the sibling ontology at the same tag before WIDOCO runs, so the
documentation of a release describes that release rather than whatever w3id
happens to serve while the build is running, and nothing is fetched.

Requires git and rdflib; --widoco additionally requires java. Run from repo root:
python scripts/build_pages.py site [--widoco widoco.jar]
"""

import html
import re
import shutil
import subprocess
import sys
import tempfile
import urllib.parse
from pathlib import Path

from rdflib import Graph, URIRef
from rdflib.namespace import OWL, RDF, RDFS

DERIVED = [("nt", "nt", "application/n-triples"), ("rdf", "xml", "application/rdf+xml"), ("jsonld", "json-ld", "application/ld+json")]
MEDIA = {"ttl": "text/turtle", "jsonld": "application/ld+json", "nt": "application/n-triples", "rdf": "application/rdf+xml"}
TAG = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
IMPORTS = re.compile(r"owl:imports <([^>]+)>")
ENTITY = re.compile(r'<div class="entity" id="([^"]+)"')
WIDOCO_FLAGS = ["-rewriteAll", "-getOntologyMetadata", "-noPlaceHolderText", "-lang", "en", "-uniteSections"]


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


def is_ontology(name):
    return name.endswith(".ttl") and ".shapes." not in name and ".instances." not in name


def declared_terms(graph):
    """Named classes and properties this file declares, as IRIs."""
    return {s for kind in (OWL.Class, OWL.DatatypeProperty, OWL.ObjectProperty)
            for s in graph.subjects(RDF.type, kind) if isinstance(s, URIRef)}


def widoco(jar, ttl, imports, out):
    """Document one ontology into `out`. `imports` maps an ontology IRI to the file
    for it at this tag; every owl:imports in the source must be in that map, so the
    import resolves locally and this release is documented against itself. WIDOCO
    has no flag to stop OWLAPI dereferencing an import, and a catalog-v001.xml next
    to the file is ignored - measured 2026-09-04 - so the IRI is rewritten instead."""
    source = ttl.read_text(encoding="utf-8")
    for iri in IMPORTS.findall(source):
        if iri not in imports:
            raise RuntimeError(f"{ttl.name}: imports {iri}, which is not an ontology at this tag")
        old = f"owl:imports <{iri}>"
        if source.count(old) != 1:
            raise RuntimeError(f"{ttl.name}: expected one {old}, found {source.count(old)}")
        source = source.replace(old, f"owl:imports <{imports[iri].resolve().as_uri()}>")

    with tempfile.TemporaryDirectory() as tmp:
        local = Path(tmp, ttl.name)
        local.write_text(source, encoding="utf-8")
        subprocess.run(["java", "-jar", str(jar), "-ontFile", str(local),
                        "-outFolder", str(Path(tmp, "widoco")), *WIDOCO_FLAGS],
                       check=True, capture_output=True, text=True)
        shutil.move(str(Path(tmp, "widoco", "doc")), str(out))


def coverage(graph, out):
    """Every term the ontology declares must have an entity div, except the terms
    that carry no rdfs:label: WIDOCO drops those silently, and gen-owl emits a bare
    declaration for a name declared on more than one class (overlay schema, D19).
    Measured at v0.2.0 and v0.3.0, all three ontologies: the two sets are equal.
    Any other gap fails the build rather than becoming a footnote."""
    divs = {urllib.parse.unquote(i)
            for i in ENTITY.findall(Path(out, "index-en.html").read_text(encoding="utf-8"))}
    missing, unlabelled = set(), set()
    for iri in declared_terms(graph):
        name = urllib.parse.unquote(str(iri).rsplit("/", 1)[-1])
        if name not in divs and urllib.parse.unquote(str(iri)) not in divs:
            missing.add(name)
        if (iri, RDFS.label, None) not in graph:
            unlabelled.add(name)
    if missing != unlabelled:
        raise RuntimeError(f"{out.name}: undocumented {sorted(missing)}, unlabelled {sorted(unlabelled)}")
    return sorted(missing)


argv = sys.argv[1:]
jar = None
if "--widoco" in argv:
    i = argv.index("--widoco")
    jar = Path(argv[i + 1])
    del argv[i:i + 2]
    if not jar.is_file():
        raise RuntimeError(f"no such file: {jar}")
site = Path(argv[0])
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
    ontologies = {}
    for name in root_files:
        if not (name.endswith(".ttl") or name.endswith(".jsonld")):
            continue
        content = subprocess.run(["git", "show", f"{tag}:{name}"], check=True, capture_output=True).stdout
        (out / name).write_bytes(content)
        served.append(name)
        if name.endswith(".ttl") and ".shapes." not in name:
            graph = Graph().parse(data=content, format="turtle")
            base = name[: -len(".ttl")]
            if is_ontology(name):
                ontologies[name] = graph
            for ext, fmt, _ in DERIVED:
                derived = out / f"{base}.{ext}"
                derived.write_text(graph.serialize(format=fmt), encoding="utf-8")
                served.append(derived.name)
    docs = []
    if jar and ontologies:
        imports = {str(iri): out / name
                   for name, graph in ontologies.items()
                   for iri in graph.subjects(RDF.type, OWL.Ontology)}
        for name, graph in sorted(ontologies.items()):
            base = name[: -len(".ttl")]
            doc = out / f"doc-{base}"
            widoco(jar, out / name, imports, doc)
            omitted = coverage(graph, doc)
            docs.append((base, omitted))
            print(f"{tag}: documented {base}" + (f" ({len(omitted)} unlabelled term(s) omitted)" if omitted else ""))

    if docs:
        entries = "".join(
            f"<li><a href=\"doc-{html.escape(base)}/index-en.html\"><code>{html.escape(base)}</code></a>"
            + (f" &mdash; not documented, because the ontology gives them no label: "
               f"<code>{html.escape(', '.join(omitted))}</code>" if omitted else "")
            + "</li>"
            for base, omitted in docs
        )
        documentation = (
            "<h2>Ontology documentation</h2>"
            f"<ul>{entries}</ul>"
            "<p>Generated with WIDOCO from the ontology at this release, with its imports resolved "
            "against the sibling ontology here rather than over the network. Individuals have no "
            "page of their own yet; an individual's IRI resolves to the instance graph that describes it.</p>"
        )
    else:
        documentation = ("<p>Per-IRI HTML descriptions are not rendered yet; "
                         "every IRI resolves to the graph that describes it.</p>")

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
        + documentation,
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
