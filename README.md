# cosmos-rdf

An RDF/OWL rendering of CDISC COSMoS — Biomedical Concepts and SDTM Dataset
Specializations — generated mechanically from the artifacts CDISC publishes in
[cdisc-org/COSMoS](https://github.com/cdisc-org/COSMoS), plus an overlay graph
for qualified ("sibling") biomedical concepts.

**Status: P4, overlay rendered.** Ten deliverables at repo version 0.3.0: two
core OWL graphs, two JSON-LD contexts, two SHACL shapes graphs, the BC instance
graph, and the overlay's own OWL graph, instance graph and shapes graph. The Dataset
Specialization A-Box is deferred (decision D4). The phase list below states intent
for the rest; none of it is a promise.

The namespace `https://w3id.org/cdisc/cosmos/` is **registered** (w3id PR #6642,
merged 2026-09-04): every IRI resolves to the document that describes it, with
content negotiation over Turtle, N-Triples, RDF/XML and JSON-LD, from a GitHub
Pages site rebuilt from the release tags (`docs/iri-and-governance.md`,
"Resolution"). `dss/` is reserved and not yet registered (D4). This repo carries the same offer
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
| P4 | Overlay: the qualified concepts as RDF | **done** — six concepts, eight recordings, three admitted result scales (D13–D23) |
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
├── cosmos_qbc_v1.ttl                # overlay T-Box: the qualified-BC schema as OWL
├── cosmos_qbc_v1.instances.ttl      # overlay A-Box: six qualified concepts, eight recordings
├── cosmos_qbc_v1.shapes.ttl         # overlay SHACL; enum constraints repaired and tightened (D24)
├── overlay/
│   ├── qbc.schema.yaml              # authored LinkML schema for the overlay
│   ├── scales.instances.yaml        # the three result scales the overlay admits, NCIt-anchored (D23)
│   ├── glucose.instances.yaml       # authored instances, first worked case
│   └── hcvrna.instances.yaml        # authored instances, second worked case
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
│   ├── 65_compare_render_paths.ipynb # direct renderer vs linkml-convert (D8)
│   ├── 70_generate_qbc.ipynb        # overlay T-Box, after 10 and 20
│   ├── 75_render_qbc.ipynb          # overlay A-Box, after 70 and 50; asserts the join to core
│   ├── 77_generate_qbc_shapes.ipynb # overlay SHACL, after 70; the D24 repair
│   ├── 78_validate_qbc_instances.ipynb # overlay conformance report; every violation classified
│   └── 80_generate_htaccess.ipynb   # the w3id .htaccess, term rules derived from the overlay T-Box
├── docs/
│   ├── source-verification.md       # the P0 gate: what was verified, and how
│   ├── decisions.md                 # D1–D24, all settled
│   ├── iri-and-governance.md        # namespace, identity, handoff, the resolution rule set
│   ├── htaccess.txt                 # the /cdisc/cosmos/ .htaccess to submit to w3id — generated by 80_
│   ├── htaccess-header.txt          # its authored header
│   ├── w3id-readme.md               # its README
│   └── known-gaps.md                # upstream gaps and current scope exclusions
├── scripts/
│   ├── ci_check.py                  # deliverable integrity guard; rdflib only
│   ├── htaccess_check.py            # every w3id IRI x six client profiles against docs/htaccess.txt
│   ├── build_pages.py               # the Pages site from every release tag; derives nt/rdf/jsonld
│   └── LINEAGE.md                   # what gets copied from usdm-rdf, and when
├── .github/workflows/
│   ├── check.yml                    # runs ci_check.py on push and pull request
│   └── pages.yml                    # rebuilds the GitHub Pages site from every release tag
├── requirements.txt                 # the notebook pipeline's environment
├── reports/                         # CSV reports from validation runs
├── queries/                         # reusable SPARQL (none yet)
└── versions/                        # deliverable snapshots per pin bump (none yet)
```

## Reproduce

Requires the packages in `requirements.txt` — `linkml` (pinned to 1.11.1, and
asserted by the generating notebooks), `rdflib`, `pandas`, `pyshacl`, `pyyaml`. Consuming the deliverables needs none of
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
8. Open `notebooks/70_generate_qbc.ipynb`. Run all cells. `cosmos_qbc_v1.ttl`
   appears at the repo root. It imports the patched BC model step 2 wrote to
   `build/`, so it runs after step 2.
9. Open `notebooks/75_render_qbc.ipynb`. Run all cells. `cosmos_qbc_v1.instances.ttl`
   appears at the repo root, and the notebook asserts that the overlay joins the
   core A-Box from step 5.
10. Open `notebooks/77_generate_qbc_shapes.ipynb`. Run all cells.
    `cosmos_qbc_v1.shapes.ttl` appears at the repo root, with the enum constraints
    repaired and the result-scale lists tightened to the admitted set (D24).
11. Open `notebooks/78_validate_qbc_instances.ipynb`. Run all cells. It reports
    the overlay's non-conformance to its own shapes, classified, and asserts that
    the repaired constraints produce no result.
12. Optional, not a build step: `notebooks/80_generate_htaccess.ipynb` regenerates
    `docs/htaccess.txt` from the overlay T-Box, and `python scripts/htaccess_check.py`
    resolves every w3id IRI in the deliverables against it.

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
| `owl:versionIRI` | `…/cosmos/bc/0.3.0` | `…/cosmos/sdtm/0.3.0` |
| term namespace (`vann:preferredNamespaceUri`) | `https://www.cdisc.org/cosmos/biomedical_concept_v1.0/` | `https://www.cdisc.org/cosmos/sdtm_v1.0/` |

Every class and property IRI is the one the published schema declares. This
rendering renames nothing; it mints a name for itself and for its releases only.
The ontology IRI and the term namespace differing is the point of the decision,
not an oversight — and `30_validate.ipynb` guards it, failing if any term ever
appears in the w3id namespace.

**Where this repo does mint under w3id, each case is a decision and a guard admits
it by name.** In the core A-Box: a category label-node at `…/bc/category/{token}`
(D18) and a concept's use of a data element concept at `…/bc/{BC}/dec/{DEC}`
(D21) — neither names anything CDISC named. In the overlay: the qualified
concepts and the overlay's own terms under `…/qbc/` (D13), and a recording's
subject, which *is* the Dataset Specialization IRI `…/dss/{DOMAIN}/{MNEMONIC}`
(D3, D17); and the three result scales the overlay admits at `…/qbc/scale/{value}`,
anchored to NCIt (D23). `scripts/ci_check.py` fails on any w3id IRI outside those
forms.

| | `cosmos_qbc_v1.ttl` |
|---|---|
| ontology IRI | `https://w3id.org/cdisc/cosmos/qbc/` |
| `owl:versionIRI` | `…/cosmos/qbc/0.3.0` |
| `owl:imports` | `…/cosmos/bc/` |
| term namespace | `https://w3id.org/cdisc/cosmos/qbc/` — the overlay's terms are its own |

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

`cosmos_bc_v1.instances.ttl`: 63,030 triples — 1,469 concepts, 224 data element
concepts plus 6,004 (concept, DEC) use-nodes carrying `dataType` and `exampleSet`
(D21), 405 category label-nodes (D18), 97 codings, 1,166 parent edges, no blank
nodes.

`cosmos_qbc_v1.ttl`: 725 triples, 10 classes, importing the core BC ontology.
`cosmos_qbc_v1.instances.ttl`: 515 triples — 6 qualified concepts, 8 recordings,
3 admitted result scales, 32 external mappings (28 on concepts, 4 NCIt scale
anchors), 15 DEC uses, 9 admissible-specimen uses, 5 interpretation-regime
assertions; every `skos:broader` lands on a concept the core A-Box renders, no
NCIt concept is the subject of an overlay triple (D22), and every `resultScale`
is one of the three scales the overlay admits (D23).
`cosmos_qbc_v1.shapes.ttl`: 366 triples, 9 closed node shapes, 42 property shapes;
the three `sh:in` lists hold IRIs, and the two result-scale lists hold exactly the
admitted set (D24).

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
the guarantees the decisions rest on: no malformed IRI in a CDISC namespace; in
the core T-Boxes nothing but the ontology and its version in the w3id namespace;
in the A-Boxes and the overlay, every w3id IRI in a form a decision admits by
name; no `dataType` on a shared DEC node; and the overlay's join to core. It runs
in CI on every push.

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
`60_validate_instances.ipynb` classifies all **41,620** violations into six causes,
failing only if one appears that is not accounted for.

| count | cause |
|---|---|
| 1,693 × 2 | `sh:closed true` rejects `skos:exactMatch` and `dcterms:identifier` — identity the schema has no slot for |
| 8,742 | `sh:in ("bc")` expects enum values as string literals; the OWL T-Box declares them as class IRIs |
| 1,166 × 2 | `parentConceptId` is `range: string`, so rendering the parent reference as a link violates datatype and node kind |
| ~190 | one node typed as both BC and DEC, each closed shape rejecting the other's slots (D12) |
| 4,366 × 2 | `categories` is `range: string`; the A-Box renders a category as a label-node (D18) |
| 6,004 × 3 + 224 | the use-node's `conceptId` is an edge, not a bare C-code; and the shared DEC node carries no `dataType`, where the shape requires exactly one (D21) |

Most of these are the same thing seen several times: **the published constraints
describe a document, not a graph.** `gen-owl` and `gen-shacl`, from one schema,
disagree about what an enum value is. A parent reference typed as a string means
that turning it into an edge is, by the model's own rules, an error. Conforming
would mean the graph stops being a graph. The last two causes are the sharpest:
CDISC's own article says `categories` is how related concepts are gathered, and
CDISC's own shape says it is a string; and the shape requires exactly one
`dataType` on a data element concept that, at this pin, has up to seven.

The overlay A-Box does not conform to its own shapes either — **130** results in
`78_validate_qbc_instances.ipynb`, all classified, none unexplained — but there the
enum disagreement is repaired rather than recorded (D24), so the constraints D23
rests on produce no result at all. The rest are the graph-over-document decisions
seen from the shapes side: C-codes rendered as edges, SKOS predicates beside the
schema's slots, the DSS IRI as a recording's subject, and the two SDTM stand-ins
where `gen-shacl` and `gen-owl` read `class_uri` and `slot_uri` differently (D19).

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
