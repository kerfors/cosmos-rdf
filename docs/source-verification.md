# P0 source verification

**Run 2026-09-01.** The P0 gate named in the kickoff brief: confirm that every
input this repo depends on has a canonical public URL, can be fetched
non-interactively, and can be pinned. If any input had to be obtained by hand,
the "mechanical rebuild" claim in `README.md` would be false and the governance
offer would not stand.

Verdict: **all four inputs fetch non-interactively and can be pinned by commit
SHA.** One finding about the upstream (no tags or releases) changes the pinning
mechanism relative to `usdm-rdf`. One finding about `cdisc-for-ai` confirms the
self-containment rule was necessary.

## 1. The four inputs

Upstream repo: `cdisc-org/COSMoS`, published under the MIT License.

| Input | Path in repo | Role |
|---|---|---|
| BC export | `export/cdisc_biomedical_concepts_latest.csv` | BC A-Box |
| DSS export | `export/cdisc_sdtm_dataset_specializations_latest.csv` | DSS A-Box |
| BC model | `model/cosmos_bc_model.yaml` | BC T-Box |
| DSS model | `model/cosmos_sdtm_model.yaml` | DSS T-Box |

Two URL forms serve the exports. Both return HTTP 200 without credentials:

- GitHub Pages: `https://cdisc-org.github.io/COSMoS/export/<file>.csv`
  — always the current publication. **Not pinnable.**
- Raw content at a commit:
  `https://raw.githubusercontent.com/cdisc-org/COSMoS/<sha>/export/<file>.csv`
  — **pinnable**, and the form this repo uses.

The models are only available on raw content; there is no Pages route.

## 2. Finding — COSMoS publishes no tags and no releases

`GET /repos/cdisc-org/COSMoS/tags` and `/releases` both return an empty list
(checked 2026-09-01). `usdm-rdf` pins DDF-RA by release tag (`v4.0.0`); that
mechanism does not exist here.

**Consequence:** the pin is a **commit SHA**, not a tag. This is a stronger pin,
not a weaker one — a SHA is immutable where a tag can be moved — but it is less
legible, so the notebook records the commit date and message alongside the SHA,
and `README.md` states the package the SHA carries.

Pinned for the first build:

```
COSMOS_COMMIT = 031429b1d14823721991cd23ee88a11616686ce3
              (2026-07-21T14:35:11Z, "Remove 'utilities/' from exclude list")
```

This is `main` HEAD at verification time. The four files last changed at:

| Path | Last-changed commit | Date | Message |
|---|---|---|---|
| `export/cdisc_biomedical_concepts_latest.csv` | `fde5c1e` | 2026-07-16 | Fix Package 18 typo |
| `export/cdisc_sdtm_dataset_specializations_latest.csv` | `785c031` | 2026-07-14 | Finalize package 18 |
| `model/cosmos_bc_model.yaml` | `a0a9f86` | 2026-01-13 | DHT draft |
| `model/cosmos_sdtm_model.yaml` | `a0a9f86` | 2026-01-13 | DHT draft |

One SHA co-pins all four, the way one DDF-RA tag co-pins `dataStructure.yml`
and `USDM_CT.xlsx` in `usdm-rdf`. Bumping it is a deliberate action.

## 3. Package identity is per row, not per file

`package_date` is a **column**, not file-level metadata. Both exports are
cumulative and carry every package a concept was published in:

- BC export: 16 distinct `package_date` values, 2023-03-31 … **2026-07-14**
- DSS export: 7 distinct `package_date` values, 2024-12-16 … **2026-07-14**

So "package date" for provenance purposes is `max(package_date)` = **2026-07-14**,
Package 18. The fetch notebook derives it rather than declaring it.

## 4. Measurements at the pinned SHA

Reproduced 2026-09-01 against `031429b1`. These confirm the figures the kickoff
brief measured on 2026-08-30, and correct one.

| Measure | Value |
|---|---|
| BC export | 6,306 rows x 17 columns |
| DSS export | 13,922 rows x 32 columns |
| Distinct `bc_id` (BC export) | 1,475 |
| Distinct `vlm_group_id` (DSS export) | 1,475 |
| Distinct `(domain, vlm_group_id)` | 1,475 |
| Distinct `bc_id` referenced by DSS | 1,008 |
| Domains | 32 |
| DSS row blocks vs groups | 1,475 vs 1,475 — **0 interleaved** |
| `vlm_group_id` appearing in more than one domain | **0** |
| `value_list` non-blank / containing `;` | 3,000 / 2,729 |
| `subset_codelist` non-blank / containing `;` | 296 / **0** |
| `subset_codelist` values that are a stringified dict | **0** |
| `assigned_value` containing `;` | **1** |
| Reification quad complete (4/4) | **13,585** |
| Reification quad empty (0/4) | 337 |
| Reification quad partial | **0** |
| `v_order` column present | **No** |

**Correction to the brief.** The brief carried an r17 fan-out figure (76 of 754
BCs with more than one DSS, maximum 92:1) and said to recount at fetch. Recounted
at Package 18, on the basis "distinct `vlm_group_id` per `bc_id`":

- **91 of 1,008** referenced BCs carry more than one DSS
- maximum fan-out **128:1**, `C181398` (allergen-specific IgE) — same concept as
  before, larger fan-out

467 of the 1,475 BCs are referenced by no DSS at all.

## 5. Finding — `cdisc-for-ai` obtained its COSMoS downloads by hand

Checked because the brief asked: if anything in `cdisc-for-ai/downloads/` was
obtained by hand rather than by a repeatable fetch, the "mechanical" claim
quietly breaks.

It was. `cdisc-for-ai/cosmos-bc-dss/downloads/` holds
`cdisc_biomedical_concepts_latest.xlsx` and
`cdisc_sdtm_dataset_specializations_latest.xlsx` with **no fetch code, no
recorded URL, no retrieval date, and no checksum sidecar**. The only network
fetch anywhere in the `cosmos-bc-dss/` and `cosmos-graph/` notebooks is the LOINC
cross-check. The `staging_2026-05/` folder is a manual sync with a hand-written
diff note.

This is not a defect in `cdisc-for-ai` — that repo is analysis, and a
hand-downloaded input is fine there. It is the evidence for why the
self-containment rule is a rule here: a repo offered for transfer to CDISC
governance cannot depend on a file whose provenance is "downloaded on some
Saturday".

## 6. What this does not verify

- The **LinkML generators** (`gen-owl`, `gen-shacl`, `gen-jsonld-context`) were
  probed on 2026-08-30 against `sibling_bc.schema.yaml`, not re-run here. Their
  results, including the six-duplicated-names blocker, are recorded in
  `known-gaps.md` and are P1/P2 work.
- Nothing about **LOINC or NCIt** content. No claim in this repo about either is
  verified yet.
- The **un-flattening** of the CSV into the nested DSS shape. Contiguity and
  quad completeness say it is feasible; the port itself is P3.
