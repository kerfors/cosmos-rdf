# scripts/ — lineage

The kickoff brief says `usdm-rdf`'s `scripts/ci_check.py` and
`scripts/postprocess_widoco.py` get copied here with lineage noted, and that no
shared tooling repo is factored out yet — two consumers is not enough to justify
one. That still holds. What follows is when each copy happens.

Neither is copied at P0, because both are specific to artifacts that do not
exist here yet, and a copy that fails on first run is worse than an absent file.

## `ci_check.py` — copy at P1

Upstream: `usdm-rdf/scripts/ci_check.py`.

Its body is entirely USDM baselines — expected triple count, named-class count,
NodeShape counts, the JSON-LD context invariant — checked against four named
deliverables at repo root. There is nothing in it to run until this repo has its
first deliverable. Copy the *shape* of it (fail-fast `check(name, actual,
expected)`, baselines declared at the top, non-zero exit on failure) when P1
produces the first Turtle, and state in its docstring that the baselines are a
third copy of the numbers in the validation notebook and README.

## `postprocess_widoco.py` — copy at P5

Upstream: `usdm-rdf/scripts/postprocess_widoco.py`.

Injects project metadata into WIDOCO HTML: preferred term, NCIt anchor, and the
six `usdm:*` annotation properties. Both the namespace constant and the
annotation set are USDM-specific, and this repo has not yet decided its own
annotation namespace (see `docs/iri-and-governance.md`, "Not decided here").
The reusable parts are the fail-fast contract — every entity div must resolve to
an IRI in the graph, and every named entity in the graph must have a div — and
the NCIt dual-anchor pair check. Copy at P5 when there is HTML to render.
