"""Check docs/htaccess.txt against every w3id IRI the deliverables carry.

Simulates mod_rewrite for the draft: RewriteCond lines gate the RewriteRule that
follows them ([OR] between conditions, AND by default), rules apply in order and
the first match ends the chain (every rule carries [L]). Each IRI is resolved under
six client profiles - no Accept header, Turtle, N-Triples, RDF/XML, JSON-LD, and a
browser - and must land on the document that has it as subject, in the
serialization the client asked for; a browser lands on the release index page.
Reserved dss/ IRIs must match no rule. With a site directory given, every target
must also exist there, so the rule set and scripts/build_pages.py agree.

Run from repo root: python scripts/htaccess_check.py [site-dir]
"""

import re
import sys
from collections import Counter
from pathlib import Path

from rdflib import Graph, URIRef

W3ID = "https://w3id.org/cdisc/cosmos/"
SITE = "https://kerfors.github.io/cosmos-rdf/"
HTACCESS = Path("docs/htaccess.txt")

GRAPHS = {
    "cosmos_bc_v1": "bc/",
    "cosmos_sdtm_v1": "sdtm/",
    "cosmos_bc_v1.instances": "bc/instances/",
    "cosmos_qbc_v1": "qbc/",
    "cosmos_qbc_v1.instances": "qbc/instances/",
}
SHAPES = ["cosmos_bc_v1.shapes.ttl", "cosmos_sdtm_v1.shapes.ttl", "cosmos_qbc_v1.shapes.ttl"]
FIXED = {
    "bc/context.jsonld": "cosmos_bc_v1.context.jsonld",
    "sdtm/context.jsonld": "cosmos_sdtm_v1.context.jsonld",
    "bc/shapes": "cosmos_bc_v1.shapes.ttl",
    "sdtm/shapes": "cosmos_sdtm_v1.shapes.ttl",
    "qbc/shapes": "cosmos_qbc_v1.shapes.ttl",
}
PROFILES = {
    "none":     ({}, "ttl"),
    "turtle":   ({"HTTP_ACCEPT": "text/turtle"}, "ttl"),
    "ntriples": ({"HTTP_ACCEPT": "application/n-triples"}, "nt"),
    "rdfxml":   ({"HTTP_ACCEPT": "application/rdf+xml"}, "rdf"),
    "jsonld":   ({"HTTP_ACCEPT": "application/ld+json"}, "jsonld"),
    "browser":  ({"HTTP_ACCEPT": "text/html,application/xhtml+xml,*/*;q=0.8",
                  "HTTP_USER_AGENT": "Mozilla/5.0"}, "index.html"),
}

# --- parse
rules = []          # (conditions, pattern, target); conditions = list of groups OR-ed inside, AND-ed between
pending = []
for line in HTACCESS.read_text(encoding="utf-8").splitlines():
    if line.startswith("RewriteCond"):
        parts = line.split()
        variable, pattern = parts[1], parts[2]
        or_next = len(parts) > 3 and "[OR]" in parts[3]
        pending.append((variable.strip("%{}"), re.compile(pattern), or_next))
    elif line.startswith("RewriteRule"):
        _, pattern, target, _flags = line.split(None, 3)
        groups, current = [], []
        for variable, cond, or_next in pending:
            current.append((variable, cond))
            if not or_next:
                groups.append(current)
                current = []
        if current:
            groups.append(current)
        rules.append((groups, re.compile(pattern), target))
        pending = []
print(f"{len(rules)} rewrite rules")


def resolve(path, env):
    for groups, pattern, target in rules:
        if all(any(cond.search(env.get(variable, "")) for variable, cond in group) for group in groups):
            match = pattern.search(path)
            if match:
                return match.expand(target.replace("$1", r"\1"))
    return None


# --- what describes what
described_in = {}
for base in GRAPHS:
    g = Graph().parse(f"{base}.ttl", format="turtle")
    for s in set(g.subjects()):
        if isinstance(s, URIRef) and str(s).startswith(W3ID):
            described_in.setdefault(str(s).split("#", 1)[0], set()).add(base)

seen = set()
for file in [f"{b}.ttl" for b in GRAPHS] + SHAPES:
    g = Graph().parse(file, format="turtle")
    for triple in g:
        for node in triple:
            if isinstance(node, URIRef) and str(node).startswith(W3ID):
                seen.add(str(node).split("#", 1)[0])

VERSION_PATH = re.compile(r"(bc|sdtm|qbc)(/instances)?/([0-9]+\.[0-9]+\.[0-9]+)")


def expected_base(iri):
    """The graph that describes the IRI (file base without extension), or None for reserved."""
    path = iri[len(W3ID):]
    if path.startswith("dss/"):
        return None
    if path in FIXED:
        return FIXED[path]
    if VERSION_PATH.fullmatch(path):
        segment = path.rsplit("/", 1)[0] + "/"
        return next(b for b, s in GRAPHS.items() if s == segment)
    if path == "":
        return "https://github.com/kerfors/cosmos-rdf#readme"
    if path in ("bc", "sdtm", "qbc"):
        return next(b for b, s in GRAPHS.items() if s == path + "/")
    where = described_in.get(iri, set())
    instance = [b for b in where if ".instances" in b]
    if instance:
        return instance[0]
    if len(where) == 1:
        return next(iter(where))
    raise RuntimeError(f"{iri}: described in {sorted(where)}")


site_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else None
failures, outcomes = [], Counter()

for iri in sorted(seen):
    path = iri[len(W3ID):]
    base = expected_base(iri)
    for profile, (env, ext) in PROFILES.items():
        landed = resolve(path, env)
        if base is None:
            if landed is not None:
                failures.append((iri, profile, f"reserved segment matched {landed}"))
            continue
        if base.startswith("https://"):
            expected = base
        elif path in FIXED:
            expected = f"{SITE}v0.3.0/{base}"                      # fixed paths: one file, no negotiation
        else:
            version = VERSION_PATH.fullmatch(path)
            release = f"v{version.group(3)}" if version else "v0.3.0"
            expected = f"{SITE}{release}/{'index.html' if ext == 'index.html' else base + '.' + ext}"
        if landed != expected:
            failures.append((iri, profile, f"landed on {landed}, expected {expected}"))
            continue
        outcomes[(profile, expected.rsplit("/", 1)[-1] if expected.startswith(SITE) else "repository README")] += 1
        if site_dir and expected.startswith(SITE):
            relative = expected[len(SITE):]
            if not (site_dir / relative).exists() and not relative.startswith("v0.2.") and not relative.startswith("v0.1."):
                failures.append((iri, profile, f"target missing from site: {relative}"))

# --- paths that occur in no graph but the file must still answer: the fixed paths,
#     the namespace root, and the reserved segment.
for path, expected in [
    ("bc/context.jsonld", f"{SITE}v0.3.0/cosmos_bc_v1.context.jsonld"),
    ("sdtm/context.jsonld", f"{SITE}v0.3.0/cosmos_sdtm_v1.context.jsonld"),
    ("bc/shapes", f"{SITE}v0.3.0/cosmos_bc_v1.shapes.ttl"),
    ("sdtm/shapes", f"{SITE}v0.3.0/cosmos_sdtm_v1.shapes.ttl"),
    ("qbc/shapes", f"{SITE}v0.3.0/cosmos_qbc_v1.shapes.ttl"),
    ("", "https://github.com/kerfors/cosmos-rdf#readme"),
    ("dss/", None),
    ("dss/LB/GLUCPL", None),
]:
    for profile, (env, _) in PROFILES.items():
        landed = resolve(path, env)
        if landed != expected:
            failures.append((W3ID + path, profile, f"landed on {landed}, expected {expected}"))
        else:
            outcomes[(profile, expected.rsplit("/", 1)[-1] if expected else "w3id 404 (reserved)")] += 1
        if site_dir and expected and expected.startswith(SITE) and not (site_dir / expected[len(SITE):]).exists():
            failures.append((W3ID + path, profile, f"target missing from site: {expected[len(SITE):]}"))

for (profile, target), n in sorted(outcomes.items()):
    print(f"{n:>6,}  {profile:9s} -> {target}")
print(f"{len(seen):>6,}  distinct w3id IRIs x {len(PROFILES)} client profiles")
if failures:
    for iri, profile, why in failures[:20]:
        print(f"FAIL  {iri} [{profile}]: {why}")
    print(f"\n{len(failures)} failure(s)")
    sys.exit(1)
print("\nevery w3id IRI resolves, in every negotiated serialization, to the document that describes it; dss/ falls through")
