# Known gaps

Gaps in the **upstream source** and in **this repo's current scope**. Recorded as
findings, not as workarounds, and not as a roadmap — do not infer that anything
here is coming soon.

Every measured number below was produced at the pinned commit
`031429b1` (COSMoS Package 18, `package_date` 2026-07-14). Method and full
figures in [source-verification.md](source-verification.md).

## 1. Upstream — six slot names declared in both published schemas

`cosmos_bc_model.yaml` and `cosmos_sdtm_model.yaml` each declare, at top level:

```
conceptId   dataType   href   packageDate   packageType   shortName
```

Verified against the pinned models, 2026-09-01: the intersection of the two
`slots:` blocks is exactly these six. `PackageTypeEnum` is a **seventh**
collision, at enum level.

Consequences, established by probe on 2026-08-30 (linkml 1.11.1) and unchanged
at this pin:

- `gen-owl` and `gen-shacl` **tolerate** it — both qualify terms by schema.
- `gen-jsonld-context` and `linkml-convert -t ttl` **fail**:
  `Conflicting URIs (…/biomedical_concept_v1.0, …/sdtm_v1.0) for item: conceptId`.
  A JSON-LD context and an RDF conversion both need one URI per term.
- The same root cause makes import order load-bearing elsewhere: a schema
  importing both must import `cosmos_bc_model` **last**, or the DEC `dataType`
  enum is clobbered by the SDTM one (LinkML merges imports last-wins).

Two independent tools, one upstream issue. Worth reporting upstream.

## 2. Upstream — neither published schema declares a `version`

`cosmos_bc_model.yaml` and `cosmos_sdtm_model.yaml` carry an `id` and a `name`
but no `version:` key. There is no schema-declared version to record in
provenance or to carry into `owl:versionIRI`; the commit SHA is the only
version handle available.

## 3. Upstream — no tags, no releases

`cdisc-org/COSMoS` publishes neither. Pinning is by commit SHA. See
[source-verification.md](source-verification.md) §2.

## 4. Upstream — the reification vocabulary is unanchored

The DSS model publishes the reification vocabulary as controlled enums, which is
more than the BC model publishes and more than a consumer would normally get:

| Enum | Permissible values | `code_set` | Values carrying `meaning:` |
|---|---|---|---|
| `LinkingPhraseEnum` | 101 | — | 0 |
| `PredicateTermEnum` | 33 | — | 0 |
| `OriginTypeEnum` | 5 | `NCIT:C170449` | 5 |
| `OriginSourceEnum` | 4 | `NCIT:C170450` | 4 |
| `RoleEnum` | 4 | — | 0 |
| `ComparatorEnum` | 2 | — | 0 |
| `SDTMVariableDataTypeEnum` | 5 | — | 0 |

The Define-XML origin terminology is fully NCIt-anchored, at both enum and value
level. **The relationship vocabulary is not anchored at all** — no `code_set`,
no per-value `meaning`. So the 33 predicates and 101 linking phrases, which are
exactly the terms an RDF rendering wants as predicates, have no external
identity: this repo must mint IRIs for them in its own namespace and say so.
That is a gap in the standard, not in the rendering.

## 5. Flattening losses in the CSV export — measured

The published CSV is a flat view of a nested model. The kickoff brief listed the
losses; this is the measurement at the pinned commit.

| Loss | Measured | Consequence for RDF |
|---|---|---|
| Concept boundary becomes N rows per `(domain, vlm_group_id)` | 1,475 groups in 1,475 contiguous row blocks — **0 interleaved** | rebuild the DSS node by grouping; safe |
| `v_order` computed then dropped | **no order column**; row order is the only carrier of SDTM variable order | emit an explicit index derived from row order, and state the dependency — order is a file convention, not a field |
| lists `;`-joined | `value_list` 3,000 non-blank / 2,729 with `;`; `subset_codelist` 296 non-blank / **0** with `;`; **1** `assigned_value` legitimately contains `;` | no corruption today, but semicolons occur in values → split guard on `value_list`, flagging suspicious tokens |
| `subsetCodelist` stringified when an object | **0** stringified-dict values | latent; assert it at ingest rather than handle it |
| `codelist.href` dropped | — | non-issue: IRIs are minted from the C-code (decision D2) |
| reification quad flattened to four columns | **13,585 complete**, 337 empty, **0 partial** | the part that matters most for RDF survives intact |

Net: the flattening costs the RDF work nothing material. Two guards to build in
at P3 — an explicit variable index, and a `;`-split guard.

## 6. Upstream — `datasetSpecializationId` is a mnemonic, not an identity

Declared `identifier: true` in `cosmos_sdtm_model.yaml`, with pattern
`^[A-Z][A-Z0-9_]*$` — an uppercase mnemonic (`GLUCSER`, `ALBCREATURIN`), not a
resolvable code, and nothing enforces uniqueness across domains.

Measured at this pin: **0 of 1,475** `vlm_group_id` values appear in more than
one domain. So minting from the mnemonic alone would work *today*. Nothing in the
standard guarantees it will keep working. See decision D3.

This is the same gap the qualified-BC work is about, met one layer down.

## 7. This repo — nothing is generated yet

At P0 there are no deliverables. No ontology, no shapes, no context, no A-Box,
no overlay, no w3id registration, no WIDOCO rendering. The phases in
`README.md` say what is intended; nothing there is a promise.

## 8. This repo — no LOINC or NCIt claim is verified

None is made yet. When one is made it will be verified against the service or
the package first, per the working conventions in `CLAUDE.md`.
