# IRI scheme and governance

Records the IRI scheme for `cosmos-rdf` and the governance handoff to CDISC.
`README.md` and `CLAUDE.md` cross-reference here.

**Lineage.** This document is adapted from `usdm-rdf/docs/iri-and-governance.md`.
Where an argument is identical it is cited rather than restated; only the parts
that differ for COSMoS are argued here. The namespace is **not yet registered**:
the w3id PR is drafted (`docs/htaccess.txt`, `docs/w3id-readme.md`, checked by
`scripts/htaccess_check.py`) but not submitted, so no IRI in it dereferences yet.

## Ontology IRI

`https://w3id.org/cdisc/cosmos/` — slash semantics, adopted by reference from
the `usdm-rdf` argument (per-IRI dereference at the redirect layer; the
trade-off is more `.htaccess` rules, and it is bounded).

**Settled at P1 (decision D7, option A): two segments, one per deliverable —
`…/cosmos/bc/` and `…/cosmos/sdtm/` — naming the ontologies only.** The class and
property IRIs stay as CDISC published them. So this namespace holds exactly two
ontology IRIs and their version IRIs today, not a vocabulary of terms.

**Why this segment.** The DDS profile developed in `cdisc-for-ai` needs a profile
id under the same segment. One w3id PR covers both — the ontology namespace and
the profile id — so the segment is registered once and used twice.

**Why no version in the path, unlike `usdm-rdf`'s `/v4/`.** USDM has major
versions that are not the same vocabulary; COSMoS does not publish a version at
all. Neither `cosmos_bc_model.yaml` nor `cosmos_sdtm_model.yaml` declares a
`version:` key (`known-gaps.md` §2), and the repo has no tags or releases to pin
against. There is nothing to put in a version path segment that would not be
this repo's invention. Release identity therefore lives entirely in
`owl:versionIRI` / `owl:versionInfo` plus the pinned upstream commit SHA — the
generic bare-numeric `versionIRI` rewrite rule from `usdm-rdf` decision D3
carries over unchanged.

The two segments follow from decision D1 (two graphs, settled by test). The
registration is of `/cdisc/cosmos/` and covers both, plus the DDS profile id.

## Provenance instead of a version tag

`usdm-rdf` pins DDF-RA by release tag and records a SHA-256 per source file.
COSMoS offers no tag, so the pin is the **upstream commit SHA**, recorded in
`downloads/.fetch_meta_*.json` alongside the source URL, the retrieval
timestamp, the SHA-256, and the package date derived from the data
(`max(package_date)`).

A SHA is a stronger pin than a tag — it is immutable, where a tag can be moved —
but it carries no human meaning, so the package date is derived and stated
everywhere the SHA appears.

## Identity of the things being named

Three identity questions, each a decision in [decisions.md](decisions.md). The
first is settled; the other two are not:

- **Concept codes** (D2, settled 2026-09-01). A concept's subject IRI is its NCIt
  OBO PURL, with `skos:exactMatch` to the EVS identifier so `usdm-rdf` decision
  D4's "always both" rule holds. The evidence for D4 (EVS host is NXDOMAIN; NCI
  Thesaurus still declares the namespace; the OBO PURL resolves) is in
  `usdm-rdf/docs/iri-and-governance.md` and is not re-argued here. 1,469 of 1,475
  concepts arrive with such a code; the six that do not are rendered as absent
  and listed in `reports/unidentified_concepts.csv`.
- **Dataset Specializations** (D3). `datasetSpecializationId` is a mnemonic, not
  a resolvable code, and its uniqueness across domains is unguaranteed —
  measured unique today. Mint domain-scoped IRIs; carry the mnemonic as
  `dcterms:identifier`; keep the gap visible in `known-gaps.md`.
- **Relationship predicates** (no decision number yet). The 33 predicate terms
  and 101 linking phrases the DSS model publishes carry no `code_set` and no
  per-value `meaning` (`known-gaps.md` §4). Their IRIs must be minted in this
  repo's namespace. That is an authored act on top of a published vocabulary and
  it must be labelled as such. **Decision D7 has since been revisited, but not
  here** — the overlay got there first: D13 names nine classes and thirty-two
  properties under `…/cosmos/qbc/`, so the relationship predicates are no longer
  the first terms that would need a w3id name.

## Layering — what may live under this namespace

Two layers, kept apart. The distinction is the same one `cdisc-for-ai` draws
between `COSMoS_Graph.xlsx` and `COSMoS_Graph_Overlay.xlsx`.

1. **Core** — a mechanical rendering of *published* COSMoS. Not opinion: the
   standard in queryable form. This is the part offerable to CDISC governance.
2. **Overlay** — the *authored* qualified-BC layer: qualified concepts with
   resolvable IRIs, typed SKOS mappings, and interpretation-regime assertions
   that carry a subject state but deliberately no regime pointer (D15). Linked
   into core by `skos:broader` (D14).

Anything this repo decides that the standard did not — disambiguating the six
colliding slot names, minting predicate IRIs, choosing a variable order rule —
is authored content by that test, however mechanical it looks. Where such a
choice is unavoidable in the core rendering, it is named in `decisions.md` and
recorded in the deliverable's provenance rather than left implicit.

## Governance handoff

Same mechanism as `usdm-rdf`: the transfer is the redirect, not the artifact. At
any point CDISC can host the deliverables under their own infrastructure and
submit a w3id PR that changes the redirect target. No minted IRI changes; no
consumer refetches.

The offer is explicit, not implicit. Status: **not yet offered**, though there is
now something to offer — ten deliverables across core and overlay. The venue will
be the COSMoS side of CDISC rather than the USDM Governance Group; identifying the
right body is part of P5, not an assumption to record here.

## Resolution — the w3id rule set (P5, drafted 2026-09-04)

`docs/htaccess.txt` is the `/cdisc/cosmos/.htaccess` to submit; `docs/w3id-readme.md`
is its README. The w3id `/cdisc/` directory holds only `usdm/v4/`, registered to
the same contact, so `cosmos/` is a sibling under a segment already held. The file
is **generated** by `notebooks/80_generate_htaccess.ipynb` — one part of it is a
function of the overlay ontology — and **checked** by `scripts/htaccess_check.py`
against every w3id IRI the ten deliverables carry.

**The rule: an IRI resolves to a document that has it as subject.** Linked-data
rule three — look up the IRI, get useful information about that thing — applied
literally, and it decides the whole file:

- A **term** of the overlay ontology (class, property; an enum value carries `#`,
  so the enum is the term) resolves to `cosmos_qbc_v1`. The 44 terms are read from
  the T-Box and written as one alternation, so a term a later decision adds changes
  the file on the next run and is caught by the checker before the w3id PR that
  carries it. This is what settles the D13 trade-off — concepts and terms share
  `qbc/` — at the resolver: not by pattern, which cannot tell them apart, but by
  the ontology saying which names are its own.
- An **individual** — a qualified concept, a scale node, a use-node, a category
  label-node, a (concept, DEC) pair — resolves to its instance graph. Under `bc/`
  every minted IRI is one (the core's terms are CDISC's, under cdisc.org).
- An **ontology IRI** resolves to the ontology at the pinned release; a **version
  IRI** to its own release through one generic rule per graph, so a release needs
  no w3id PR (the usdm-rdf D3 rule, carried over). `sdtm/` has no instance graph
  (D4), so everything under it is the ontology. Fixed paths serve the contexts
  (`bc/context.jsonld`, `sdtm/context.jsonld`) and the shapes (`bc/shapes`,
  `sdtm/shapes`, `qbc/shapes`).
- **`dss/` is reserved and unregistered.** The recording subjects minted under it
  (D17) are stable identity, but the graph that describes them at their own grain
  is the deferred DSS A-Box (D4). Redirecting them to the overlay A-Box, which
  carries them only as subjects of the overlay's thinned view, would say
  "described" about the half that is deferred. Until D4 lands they fall through to
  the w3id 404 — dangling by design, as D17 records. Adding the segment is a
  second, one-block PR; the README names it as reserved.

**The target is the GitHub Pages site, not the raw file — because of the media
type.** `raw.githubusercontent.com` serves Turtle as `text/plain`; a client that
asked for `text/turtle` would be 303'd to a document that says it is not Turtle,
which is where `usdm-rdf`'s canonical Turtle still points. GitHub Pages serves by
extension (`application/n-triples` for `.nt` was confirmed on the usdm-rdf site).
`.github/workflows/pages.yml` rebuilds the site from **every release tag** on each
tag push (`scripts/build_pages.py`): `/vX.Y.Z/<graph>.{ttl,nt,rdf,jsonld}` per tag,
Turtle canonical and the other three derived from it at deploy, an index page per
release and one at the root. Nothing is copied by hand; the site is a function of
the tags. Enabling Pages (source: GitHub Actions) is a one-time repository setting.

**Content negotiation, over serializations that exist.** Each resolving group is
one pattern written five times: `Accept: application/n-triples`, `application/rdf+xml`
and `application/ld+json` go to the derived files; a browser (`text/html` or a
Mozilla user agent) goes to the release's `index.html`, which is where per-IRI HTML
anchors will go; everything else — `text/turtle` and no Accept header — goes to
the canonical Turtle. 56 rules.

**Checked, not assumed.** `htaccess_check.py` simulates mod_rewrite (conditions,
`[OR]`, first match wins) for 6,550 distinct w3id IRIs under six client profiles,
plus the fixed paths, the root and the reserved segment, and asserts each lands on
the document that describes it in the serialization asked for, and — given the
built site directory — that every target exists there. The `qbc/` terms land on
the ontology 47 ways (44 terms, root, bare id, version); no IRI is "reached through
an import".

**Order of operations for the PR.** Enable Pages, run the workflow once
(`workflow_dispatch`), confirm `…/v0.3.0/cosmos_qbc_v1.ttl` answers `text/turtle`,
then open the w3id PR. Submitting before the site answers would register 303s to
404s.

## Not decided here

- Per-IRI HTML descriptions (WIDOCO or a rendered page). P5, second step; the
  browser rule already points where they will live, so adding them changes
  `build_pages.py` and nothing in the `.htaccess`.
- A project annotation namespace. The P1 headers use only published vocabulary —
  Dublin Core, VANN, OWL, RDFS — so nothing has needed one yet. The first
  candidate is the relationship-predicate vocabulary above.
