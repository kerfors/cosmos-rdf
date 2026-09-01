# cosmos-rdf

An RDF/OWL rendering of CDISC COSMoS — Biomedical Concepts and SDTM Dataset
Specializations — generated mechanically from the artifacts CDISC publishes in
[cdisc-org/COSMoS](https://github.com/cdisc-org/COSMoS), plus an overlay graph
for qualified ("sibling") biomedical concepts.

**Status: P3, Biomedical Concept layer.** Seven deliverables at repo version
0.1.0: two OWL graphs, two JSON-LD contexts, two SHACL shapes graphs, and the BC
instance graph. The Dataset Specialization A-Box is deferred (decision D4) and
there is no overlay. The phase list below states intent for the rest; none of it
is a promise.

The namespace `https://w3id.org/cdisc/cosmos/` is **not yet registered**, so the
ontology IRIs below do not dereference yet. This repo carries the same offer
`usdm-rdf` carries: draft, not a normative CDISC artifact, offered for transfer to
CDISC governance — transfer is a single PR against the w3id `.htaccess`. See
[docs/iri-and-governance.md](docs/iri-and-governance.md).

## Why this repo exists

CDISC publishes COSMoS as data: two LinkML schemas (`cosmos_bc_model.yaml`,
`cosmos_sdtm_model.yaml`) and two cumulative flat CSV exports. The schemas
already carry required slots, identifier patterns, cardinality, and — at the DSS
layer — the reification vocabulary itself as controlled enums. So the gap between
published COSMoS and a queryable RDF/OWL view is largely mechanical, the same
argument `usdm-rdf` makes for USDM.

It is a separate repo rather than a folder in `cdisc-for-ai` because the
governance offer requires the artifact to be independently transferable,
independently versioned, and the target of its own namespace. A folder inside an
analysis repo is none of those. It is not part of `usdm-rdf` either: different
upstream, different namespace segment, different release cadence.

## Self-containment rule

**This repo rebuilds its deliverables from its own pinned inputs, with no
dependency on `cdisc-for-ai` or any other repo.** A repo CDISC cannot rebuild
without also cloning a personal analysis repo is not meaningfully transferable.
The handoff has to be able to say: clone this, run the notebooks, get the
artifact.

Consequences:

- `downloads/` is this repo's own, fetched by `notebooks/10_fetch_cosmos.ipynb`,
  pinned by an upstream commit SHA. Nothing is copied from `cdisc-for-ai`.
- Every input records source URL, retrieval date, SHA-256, and package date.
- **Fetch only from the public CDISC GitHub artifacts, never the CDISC Library
  API.** The API is member-gated — proven by auth test on 2026-08-05: a valid
  key, HTTP 401, body *"Members-only content"*. A member-gated dependency would
  make the pipeline non-reproducible for any non-member, which is fatal for a
  repo whose claim is mechanical reproducibility.

## Pinned source

```
COSMOS_REPO   = cdisc-org/COSMoS
COSMOS_COMMIT = 031429b1d14823721991cd23ee88a11616686ce3   (2026-07-21)
PACKAGE_DATE  = 2026-07-14   (derived: max(package_date) — Package 18)
```

`cdisc-org/COSMoS` publishes no tags and no releases, so the pin is a commit SHA
rather than a tag. One SHA co-pins all four inputs. Bumping it is a deliberate
action, not a default.

| Input | Path at the pinned commit | Role |
|---|---|---|
| BC export | `export/cdisc_biomedical_concepts_latest.csv` | BC A-Box |
| DSS export | `export/cdisc_sdtm_dataset_specializations_latest.csv` | DSS A-Box |
| BC model | `model/cosmos_bc_model.yaml` | BC T-Box |
| DSS model | `model/cosmos_sdtm_model.yaml` | DSS T-Box |

**CSV, not xlsx.** Same cumulative content, cleaner parsing, text-diffable, no
`openpyxl`, and it is the artifact CDISC generates first.

**Not the per-package `yaml/<pkg>/` folders.** They are per-package *deltas*, not
cumulative snapshots, and COSMoS publishes no public cumulative nested artifact.
The nested shape is recovered by un-flattening the CSV. Established in
`cdisc-for-ai/docs/COSMoS_Ingestion_Source.md` §3.

Verification of all of the above, with measurements:
[docs/source-verification.md](docs/source-verification.md).

## What the source carries at the pinned commit

- 1,475 Biomedical Concepts; 1,475 Dataset Specializations across 32 domains
- 1,008 BCs referenced by at least one DSS — so 467 BCs have no DSS
- 91 of those 1,008 BCs fan out to more than one DSS; maximum 128:1 (`C181398`,
  allergen-specific IgE)
- 13,585 complete reification quads, 0 partial
- The DSS model publishes 101 linking phrases and 33 predicate terms as
  controlled enums, and the Define-XML origin terminology fully NCIt-anchored.
  The relationship vocabulary itself is **not** anchored — see
  [docs/known-gaps.md](docs/known-gaps.md) §4.

## Layering

1. **Core** — mechanical RDF rendering of published COSMoS. The part offerable to
   CDISC governance.
2. **Overlay** — the authored qualified-BC layer: sibling concepts with
   resolvable IRIs, typed SKOS mappings, interpretation-regime pointers, linked
   into core by `skos:broader`.

The DDS profile in `cdisc-for-ai/cosmos-bc-dss/dds/` is a closed-world
*projection* of the same content, for a pipeline that needs a contract. One
graph, many views.

## Phases

| Phase | Content | State |
|---|---|---|
| P0 | Scaffold, source verification, `10_fetch`, decisions written | **done** |
| P1 | Core T-Box: OWL per schema, ontology headers, validation, known gaps | **done** |
| P2 | Identity binding and JSON-LD contexts | **done** |
| P3 | A-Box and shapes | **BC layer done**; DSS layer deferred (D4) |
| P4 | Overlay: the sibling concepts as RDF | not started |
| P5 | Dereference and publish: w3id PR, WIDOCO, release, CI | not started |
| P6 | The DDS profile gains a sentence saying it is a projection | not started |

P0–P2 is publishable on its own — an OWL + SHACL rendering of COSMoS does not
exist anywhere today. P3 is not committed to until P2 shows the identity binding
holds.

## Repo layout

```
cosmos-rdf/
├── README.md
├── CLAUDE.md
├── LICENSE                          # MIT — mirrors the upstream COSMoS license
├── .gitignore
├── cosmos_bc_v1.ttl                 # BC T-Box deliverable
├── cosmos_sdtm_v1.ttl               # DSS T-Box deliverable
├── cosmos_bc_v1.context.jsonld      # BC JSON-LD 1.1 instance context
├── cosmos_sdtm_v1.context.jsonld    # DSS JSON-LD 1.1 instance context
├── cosmos_bc_v1.shapes.ttl          # BC SHACL shapes, generated, unmodified
├── cosmos_sdtm_v1.shapes.ttl        # DSS SHACL shapes, generated, unmodified
├── cosmos_bc_v1.instances.ttl       # BC A-Box
├── downloads/                       # gitignored — the four pinned inputs land here
├── build/                           # gitignored — the patched BC model, derived
├── patches/
│   └── cosmos_bc_prefix.patch       # written by 20_generate; the one repair, for review
├── notebooks/
│   ├── 10_fetch_cosmos.ipynb        # pin the commit SHA, fetch four inputs, write provenance
│   ├── 20_generate.ipynb            # apply the repair, render both schemas, author the headers
│   ├── 30_validate.ipynb            # baselines, IRI checks, graph separation, contexts, reports
│   ├── 40_generate_context.ipynb    # JSON-LD 1.1 instance context per schema
│   ├── 45_identity_probe.ipynb      # the D2 evidence chain; not a build step
│   ├── 50_render_bc.ipynb           # the BC A-Box
│   ├── 55_generate_shapes.ipynb     # SHACL per schema
│   ├── 60_validate_instances.ipynb  # conformance report; every violation classified
│   └── 65_compare_render_paths.ipynb # direct renderer vs linkml-convert (D8)
├── docs/
│   ├── source-verification.md       # the P0 gate: what was verified, and how
│   ├── decisions.md                 # D1–D12, all settled
│   ├── iri-and-governance.md        # namespace, identity, handoff
│   └── known-gaps.md                # upstream gaps and current scope exclusions
├── scripts/
│   ├── ci_check.py                  # deliverable integrity guard; rdflib only
│   └── LINEAGE.md                   # what gets copied from usdm-rdf, and when
├── .github/workflows/
│   └── check.yml                    # runs ci_check.py on push and pull request
├── requirements.txt                 # the notebook pipeline's environment
├── reports/                         # CSV reports from validation runs
├── queries/                         # reusable SPARQL (none yet)
└── versions/                        # deliverable snapshots per pin bump (none yet)
```

## Reproduce

Requires the packages in `requirements.txt` — `linkml` (developed against 1.11.1),
`rdflib`, `pandas`, `pyshacl`, `pyyaml`. Consuming the deliverables needs none of
them; `scripts/ci_check.py`, which is what CI runs, needs `rdflib` alone.

1. Open `notebooks/10_fetch_cosmos.ipynb`. The upstream commit SHA is pinned in
   the first code cell. Run all cells. The four inputs land in `downloads/`, each
   with a `.fetch_meta_*.json` sidecar recording URL, SHA-256, size, retrieval
   timestamp, and — for the exports — the derived package date and row counts.
2. Open `notebooks/20_generate.ipynb`. Run all cells. `cosmos_bc_v1.ttl` and
   `cosmos_sdtm_v1.ttl` appear at the repo root.
3. Open `notebooks/40_generate_context.ipynb`. Run all cells. The two
   `*.context.jsonld` files appear at the repo root.
4. Open `notebooks/55_generate_shapes.ipynb`. Run all cells. The two
   `*.shapes.ttl` files appear at the repo root.
5. Open `notebooks/50_render_bc.ipynb`. Run all cells. `cosmos_bc_v1.instances.ttl`
   appears at the repo root.
6. Open `notebooks/30_validate.ipynb`. Run all cells. Compare against the
   baselines below; CSV reports are written to `reports/`.
7. Open `notebooks/60_validate_instances.ipynb`. Run all cells. It reports
   non-conformance — see **Conformance** below — and fails only on a violation it
   cannot account for.

`notebooks/45_identity_probe.ipynb` and `notebooks/65_compare_render_paths.ipynb`
are optional and are not build steps. The first measures the claim decision D2
rests on; the second checks the direct renderer against `linkml-convert` over the
patched schema (decision D8). Both assert their outcomes, so both fail if the
published schema changes — which would be good news, not a bug.

## IRI scheme

Decision D7, option A ([docs/decisions.md](docs/decisions.md)): **the ontology is
named under w3id, the terms are not.**

| | `cosmos_bc_v1.ttl` | `cosmos_sdtm_v1.ttl` |
|---|---|---|
| ontology IRI | `https://w3id.org/cdisc/cosmos/bc/` | `https://w3id.org/cdisc/cosmos/sdtm/` |
| `owl:versionIRI` | `…/cosmos/bc/0.1.0` | `…/cosmos/sdtm/0.1.0` |
| term namespace (`vann:preferredNamespaceUri`) | `https://www.cdisc.org/cosmos/biomedical_concept_v1.0/` | `https://www.cdisc.org/cosmos/sdtm_v1.0/` |

Every class and property IRI is the one the published schema declares. This
rendering renames nothing; it mints a name for itself and for its releases only.
The ontology IRI and the term namespace differing is the point of the decision,
not an oversight — and `30_validate.ipynb` guards it, failing if any term ever
appears in the w3id namespace.

## Expected baselines (pinned commit `031429b1`, package date 2026-07-14)

| | `cosmos_bc_v1.ttl` | `cosmos_sdtm_v1.ttl` |
|---|---|---|
| triples | 535 | 2,028 |
| top-level `owl:Class` | 6 | 24 |
| enum permissible values | 15 | 146 |
| `owl:ObjectProperty` | 5 | 13 |
| `owl:DatatypeProperty` | 13 | 30 |
| IRIs in the CDISC namespace | 40 | 205 |
| context terms | 27 | 56 |
| shapes triples | 204 | 679 |
| `sh:NodeShape` (all closed) | 3 | 7 |
| property shapes | 22 | 44 |

Of the OWL triples, 25 per graph are the authored ontology header and the
`owl:AnnotationProperty` declarations that go with it; the rest are generated. The
shapes graphs are generated in full, with nothing authored.

`cosmos_bc_v1.instances.ttl`: 29,697 triples — 1,469 concepts, 224 data element
concepts, 97 codings, 1,166 parent edges, no blank nodes.

Nine of the SDTM top-level classes are OBO PURLs (`obo:NCIT_C170547` and
siblings) rather than terms in the COSMoS namespace: the Define-XML origin
terminology, carried through from the enum `meaning:` values. They arrive already
in the resolvable form decision D2 calls for.

The Turtle deliverables are **byte-stable**: re-running `20_generate.ipynb`
against an unchanged pin reproduces them exactly, because the graphs are
canonicalized before serialization (decision D9). So a `git diff` on a deliverable
means something. Deviation from a fresh pin indicates either a source change —
likely benign, document the delta in `docs/` — or a generation bug. Investigate
before releasing.

`scripts/ci_check.py` asserts all of the above against the committed files, plus
the two guarantees the decisions rest on: no malformed IRI in a CDISC namespace,
and nothing but the ontology and its version in the w3id namespace. It runs in CI
on every push.

## Identity

Decision D2: a concept's subject IRI is its **NCIt OBO PURL**. Measured against
the pinned export, `bc_id` equals `ncit_code` in all 6,283 rows carrying both, so
**1,469 of 1,475** biomedical concepts arrive with a resolvable identifier and
nothing is invented for them.

**Six do not, and this repo renders no node for them** — `NEW_1` and
`NEW_LZZT`/`LZZT1`–`LZZT4`, plus two data element concepts. They are listed in
`reports/unidentified_concepts.csv`, derived on every run, so a deliberate gap
cannot be mistaken for an oversight.

The published schema will not convert either way without editing:
`45_identity_probe.ipynb` shows that the `conceptId` pattern
`^(C[0-9]+|NEW_[A-Z_]*[0-9]*)$` **forbids the only form that converts to RDF** —
an instance can be schema-valid or RDF-convertible, not both. That is a
constraint ruling identity out, not a missing binding.

## Conformance

The BC A-Box **does not conform** to the SHACL generated from the published
schema, and the report is the point (decision D11). The shapes ship unmodified —
they are CDISC's constraints, not this repo's opinion of them — and
`60_validate_instances.ipynb` classifies all **8,925** violations into four causes,
failing only if one appears that is not accounted for.

| count | cause |
|---|---|
| 1,693 × 2 | `sh:closed true` rejects `skos:exactMatch` and `dcterms:identifier` — identity the schema has no slot for |
| 2,962 | `sh:in ("bc")` expects enum values as string literals; the OWL T-Box declares them as class IRIs |
| 1,166 × 2 | `parentConceptId` is `range: string`, so rendering the parent reference as a link violates datatype and node kind |
| ~230 | one node typed as both BC and DEC, each closed shape rejecting the other's slots |

Three of the four are the same thing seen three times: **the published constraints
describe a document, not a graph.** `gen-owl` and `gen-shacl`, from one schema,
disagree about what an enum value is. A parent reference typed as a string means
that turning it into an edge is, by the model's own rules, an error. Conforming
would mean the graph stops being a graph.

`65_compare_render_paths.ipynb` shows the split is inside the toolchain rather
than in this repo's reading of it: over six concepts, 44 predicate comparisons
between the direct renderer and `linkml-convert` agree and 32 differ, all
documented — and on enum values and `parentConceptId`, `linkml-convert` sides with
`gen-shacl` against `gen-owl`.

## Known gaps

Read [docs/known-gaps.md](docs/known-gaps.md) before assuming anything works.
The load-bearing ones: six slot names are declared in both published schemas,
which blocks JSON-LD context generation and instance conversion; the DSS
identifier is a mnemonic rather than a resolvable code; and the relationship
vocabulary has no external anchors.

## License

MIT (see `LICENSE`). Generated content is derived from CDISC COSMoS, which CDISC
publishes under the MIT License, and is offered under the same terms with
attribution to CDISC. This differs from `usdm-rdf`, whose upstream is CC-BY-4.0.

## Acknowledgements

This project depends entirely on CDISC publishing COSMoS as LinkML schemas and
open exports. Without them the conversion would be neither mechanical nor
reproducible.
