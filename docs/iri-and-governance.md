# IRI scheme and governance

Records the IRI scheme for `cosmos-rdf` and the governance handoff to CDISC.
`README.md` and `CLAUDE.md` cross-reference here.

**Lineage.** This document is adapted from `usdm-rdf/docs/iri-and-governance.md`.
Where an argument is identical it is cited rather than restated; only the parts
that differ for COSMoS are argued here. At P0 the namespace is **not yet
registered** — no w3id PR has been submitted and no IRI in it dereferences.

## Ontology IRI

`https://w3id.org/cdisc/cosmos/` — slash semantics, adopted by reference from
the `usdm-rdf` argument (per-IRI dereference at the redirect layer; the
trade-off is more `.htaccess` rules, and it is bounded).

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

Whether the eventual layout is one namespace or two — `…/cosmos/bc/` and
`…/cosmos/sdtm/` — depends on decision D1 in [decisions.md](decisions.md), which
is open. The registered segment is the same either way.

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

Three identity questions, none of them settled at P0; each is a decision in
[decisions.md](decisions.md):

- **Concept codes** (D2). The exports carry bare C-codes, not IRIs. The proposal
  is `usdm-rdf` decision D4 unchanged: dual anchor, EVS identifier plus
  resolvable OBO PURL, always both. The evidence for that decision (EVS host is
  NXDOMAIN; NCI Thesaurus still declares the namespace; the OBO PURL resolves) is
  in `usdm-rdf/docs/iri-and-governance.md` and is not re-argued here.
- **Dataset Specializations** (D3). `datasetSpecializationId` is a mnemonic, not
  a resolvable code, and its uniqueness across domains is unguaranteed —
  measured unique today. Mint domain-scoped IRIs; carry the mnemonic as
  `dcterms:identifier`; keep the gap visible in `known-gaps.md`.
- **Relationship predicates** (no decision number yet). The 33 predicate terms
  and 101 linking phrases the DSS model publishes carry no `code_set` and no
  per-value `meaning` (`known-gaps.md` §4). Their IRIs must be minted in this
  repo's namespace. That is an authored act on top of a published vocabulary and
  it must be labelled as such.

## Layering — what may live under this namespace

Two layers, kept apart. The distinction is the same one `cdisc-for-ai` draws
between `COSMoS_Graph.xlsx` and `COSMoS_Graph_Overlay.xlsx`.

1. **Core** — a mechanical rendering of *published* COSMoS. Not opinion: the
   standard in queryable form. This is the part offerable to CDISC governance.
2. **Overlay** — the *authored* qualified-BC layer: sibling concepts with
   resolvable IRIs, typed SKOS mappings, interpretation-regime pointers. Linked
   into core by `skos:broader`.

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

The offer is explicit, not implicit. Status at P0: **not yet offered** — there
is nothing generated to offer. The venue when there is will be the COSMoS side of
CDISC rather than the USDM Governance Group; identifying the right body is part
of P5, not an assumption to record here.

## Not decided here

- Which serialization is canonical for content negotiation, and the `.htaccess`
  rule set. P5. `usdm-rdf/docs/htaccess.txt` is the reference to adapt.
- The project annotation namespace and its properties. There are no annotations
  yet because there is no generator yet.
