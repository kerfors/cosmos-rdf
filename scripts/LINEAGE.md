# scripts/ — lineage

The kickoff brief says `usdm-rdf`'s `scripts/ci_check.py` and
`scripts/postprocess_widoco.py` get copied here with lineage noted, and that no
shared tooling repo is factored out yet — two consumers is not enough to justify
one. That still holds. What follows is when each copy happens.

Neither was copied at P0, because both are specific to artifacts that did not
exist here yet, and a copy that fails on first run is worse than an absent file.

## `ci_check.py` — adapted, 2026-09-01

Upstream: `usdm-rdf/scripts/ci_check.py`.

The *shape* was copied, not the body: fail-fast `check(name, actual, expected)`,
baselines declared at the top, non-zero exit on failure, `rdflib` as the only
dependency so CI installs one package. The body is this repo's own, covering seven
deliverables rather than four.

It also carries two checks the upstream has no equivalent for, because they guard
decisions rather than counts: no malformed IRI in a CDISC namespace
(`docs/known-gaps.md` §1a), and nothing but the ontology and its version in the
w3id namespace (decision D7). Those are the two ways this repo could silently stop
being what it says it is.

`.github/workflows/check.yml` runs it on push and pull request, mirroring
`usdm-rdf`.

## `postprocess_widoco.py` — copy at P5

Upstream: `usdm-rdf/scripts/postprocess_widoco.py`.

Injects project metadata into WIDOCO HTML: preferred term, NCIt anchor, and the
six `usdm:*` annotation properties. Both the namespace constant and the
annotation set are USDM-specific, and this repo has not yet decided its own
annotation namespace (see `docs/iri-and-governance.md`, "Not decided here").
The reusable parts are the fail-fast contract — every entity div must resolve to
an IRI in the graph, and every named entity in the graph must have a div — and
the NCIt dual-anchor pair check. Copy at P5 when there is HTML to render.
