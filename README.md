# cosmos-rdf

An RDF/OWL rendering of CDISC COSMoS — Biomedical Concepts and SDTM Dataset
Specializations — generated mechanically from the artifacts CDISC publishes in
[cdisc-org/COSMoS](https://github.com/cdisc-org/COSMoS), plus an overlay graph
for qualified ("sibling") biomedical concepts.

**Status: P0 — scaffold and source verification. Nothing is generated yet.**
There is no ontology, no shapes graph, no context, no A-Box and no overlay in
this repo. What exists is the pinned source, the fetch pipeline, and the written
decisions. The phase list below states intent; none of it is a promise.

The namespace `https://w3id.org/cdisc/cosmos/` is **not yet registered**. When
there are deliverables, this repo will carry the same offer `usdm-rdf` carries:
draft, not a normative CDISC artifact, offered for transfer to CDISC governance —
transfer is a single PR against the w3id `.htaccess`. See
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
| P1 | Core T-Box: `gen-owl` per schema, validation, known gaps | not started |
| P2 | Identity binding (NCIT prefix) and JSON-LD context | not started |
| P3 | A-Box: un-flatten the CSV, render, SHACL shapes, validate | not started |
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
├── downloads/                       # gitignored — the four pinned inputs land here
├── notebooks/
│   └── 10_fetch_cosmos.ipynb        # pin the commit SHA, fetch four inputs, write provenance
├── docs/
│   ├── source-verification.md       # the P0 gate: what was verified, and how
│   ├── decisions.md                 # D1–D5, all open
│   ├── iri-and-governance.md        # namespace, identity, handoff
│   └── known-gaps.md                # upstream gaps and current scope exclusions
├── scripts/
│   └── LINEAGE.md                   # what gets copied from usdm-rdf, and when
├── reports/                         # validation reports (none yet)
├── queries/                         # reusable SPARQL (none yet)
└── versions/                        # deliverable snapshots per pin bump (none yet)
```

## Reproduce

1. Open `notebooks/10_fetch_cosmos.ipynb`. The upstream commit SHA is pinned in
   the first code cell. Run all cells. The four inputs land in `downloads/`, each
   with a `.fetch_meta_*.json` sidecar recording URL, SHA-256, size, retrieval
   timestamp, and — for the exports — the derived package date and row counts.
2. There is no step 2 yet. P1 adds `20_generate`.

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
