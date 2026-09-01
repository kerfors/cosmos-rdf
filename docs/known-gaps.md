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

## 1a. Upstream — the BC schema's namespace prefix has no trailing separator

`cosmos_bc_model.yaml` declares:

```yaml
cosmos_bc: https://www.cdisc.org/cosmos/biomedical_concept_v1.0
```

with no trailing `/` or `#`, where `cosmos_sdtm_model.yaml` declares its own
prefix **with** the slash. LinkML concatenates directly, so every IRI generated
from the BC model is malformed:

```
https://www.cdisc.org/cosmos/biomedical_concept_v1.0BiomedicalConcept
https://www.cdisc.org/cosmos/biomedical_concept_v1.0categories
```

against the SDTM model's well-formed `…/cosmos/sdtm_v1.0/assignedTerm`.

This is a one-character defect with an outsized effect: it makes the mechanical
RDF rendering of the BC layer unusable as published, and it affects any consumer
running any LinkML generator over that file, not just this repo.

**It cannot be repaired from a wrapper schema.** Redeclaring the prefix with the
slash in an importing schema is rejected —
`ValueError: Prefix: cosmos_bc mismatch between <importing schema> and COSMoS-Biomedical-Concepts-Schema`
— and `gen-owl` has no prefix-override option. So the repair is a **vendored,
patched copy** of `cosmos_bc_model.yaml`: one character, recorded as a patch
against the pinned commit, reapplied on every pin bump.

Verified 2026-09-01 — with the trailing slash added and nothing else changed,
`gen-owl` and `gen-jsonld-context` both succeed and the IRIs come out as
`https://www.cdisc.org/cosmos/biomedical_concept_v1.0/BiomedicalConcept`.

Report upstream together with §1: the fix is one character and needs no
modelling discussion.

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

## 7. This repo — the Dataset Specialization A-Box is not rendered

At P3 the deliverables are the two OWL graphs, the two JSON-LD contexts, the two
SHACL shapes graphs and `cosmos_bc_v1.instances.ttl`. **The DSS instance layer is
deferred** (decision D4): 1,475 specializations, 13,922 variables, roughly 450,000
triples. Decisions D3 and D5 govern it and are settled but not yet exercised.

There is no overlay, no w3id registration and no WIDOCO rendering. The phases in
`README.md` say what is intended; nothing there is a promise.

**The ontology IRIs do not dereference.** The w3id namespace is not registered
yet (P5), so `https://w3id.org/cdisc/cosmos/bc/` resolves to nothing today. Nor
do the term IRIs: they are CDISC's published strings, and both schema ids return
404 on `cdisc.org` (checked 2026-09-01, with `https://www.cdisc.org/cosmos/`
redirecting to a page slugged `cdisc-biomedical-concepts-old`). That half is not
this repo's to fix — see decision D7.

## 7a. Upstream — the `conceptId` pattern forbids the RDF-convertible form

`^(C[0-9]+|NEW_[A-Z_]*[0-9]*)$` admits a bare C-code and nothing else. A bare code
cannot be expanded into an IRI: `linkml-convert` fails with
`ValueError: Unknown CURIE prefix: @base`, and `id_prefixes` does not help,
because it constrains which prefixes are allowed rather than supplying one. Lift
the value to `NCIT:C115805` and conversion succeeds — but validation then fails,
because the pattern forbids the colon.

So a COSMoS instance can be **schema-valid or RDF-convertible, not both**, as
published. Measured 2026-09-01 and asserted on every run by
`45_identity_probe.ipynb`.

Report upstream with §1 and §1a. The fix is a pattern that admits a CURIE and a
`range: uriorcurie`; it is a larger change than the other two because it edits a
constraint rather than correcting a typo.

## 7b. Upstream — six concepts have no identifier at all

`NEW_1`, `NEW_LZZT`, `NEW_LZZT1`–`NEW_LZZT4`, and the data element concepts
`NEW_DEC1` and `NEW_DEC2`. The placeholder mechanism the standard provides
produces a name, not an identifier: no prefix exists to expand it, and none can.

Four of them are referenced by real dataset specializations —
`PATCHSURVEYACCEPTABILITY`, `PATCHSURVEYAPPEARANCE`, `PATCHSURVEYDURABILITY`,
`PATCHSURVEYSIZE` in domain QS, 32 rows — and `NEW_DEC1` by
`SURGMARGSTATBREAST`. Under decision D2 this repo renders no node for them, so
those references will have no target in the A-Box; P3 decides how to say so.

Full list, derived on every run: `reports/unidentified_concepts.csv`.

This is the gap the qualified-BC work exists for, met in the standard's own
example study.

## 7c. Upstream — a fifth export exists and is fully derivable

`export/cdisc_biomedical_concepts_hierarchy_latest.csv` is published alongside the
four pinned inputs: one row per BC, adding `bc_short_name_id`,
`bc_hierarchy_level`, `bc_hierarchy_full` and `dec_n`.

**It is not fetched, because it adds no information.** All three derived columns
reconstruct exactly from the flat export by walking `parent_bc_id` — 1,475 of
1,475 on each, measured 2026-09-01. Both files carry the same 1,475 concepts, with
none unique to either. It carries no `package_date` column, so its provenance
could not be derived the way the other inputs' is.

Recording it here so a later reader does not think it was overlooked. The
reconstruction check is also why `50_render_bc.ipynb` can take a concept's state
from its rows at the latest `package_date` without asserting that rule: the
publisher's own view agrees with it.

## 7d. This repo — the A-Box does not conform to the published shapes

8,925 violations, four causes, every one classified by
`60_validate_instances.ipynb` and recorded in `reports/shacl_conformance.csv`. The
full argument is decision D11. In short: `sh:closed true` rejects the identity
triples the schema has no slot for; `gen-owl` and `gen-shacl` disagree about
whether an enum value is a class IRI or a string; and `parentConceptId` is typed
`string`, so rendering it as an edge is an error by the model's own rules.

Not a defect to fix. Conforming would mean parent references stay strings and the
NCIt anchoring leaves the data.

## 7e. Upstream — nineteen concepts are used at two layers

Nineteen NCIt codes are both a Biomedical Concept and a Data Element Concept, so
they resolve to one node carrying both types. For Race `C17049`, Sex `C28421` and
Ethnic Group `C16564` that is correct — each is a BC with one DSS in DM and a DEC
on one DM variable, so the concept is the whole content of the observation.

The other sixteen are a curation observation, not a modelling problem: fifteen have
no DSS of their own as a BC, and nine appear in no DSS in either role. Only two
have labels that disagree, and only by a `[RETIRED]` suffix carried in the BC label
and absent from the DEC label.

Reported, not resolved: `reports/dual_role_concepts.csv`, derived on every run.

## 7f. This repo — `categories` is rendered as literals, and that drops a grouping mechanism

`cosmos_bc_v1.instances.ttl` emits `categories` as **4,389 string literals over
408 distinct tokens** — `QRS` carried by 291 concepts, `Laboratory Tests` by 186,
104 tokens used exactly once. So the attribute that connects concepts to one
another is flat text, and the BC layer cannot be traversed by classification.

That followed the schema's `range: string` and was never argued. It should have
been, because the publisher has documented the opposite.

CDISC's knowledge-base article *Searching CDISC Biomedical Concepts*
(<https://www.cdisc.org/kb/articles/cdisc-published/searching-cdisc-biomedical-concepts>)
states that the NCIt hierarchy "does not consistently align with CDISC-specific
needs", that "relying on NCIt alone is not sufficient for locating all BCs
associated with a specific QRS instrument", and that the `categories` attribute is
what carries the grouping. Of synonyms it says plainly: "it does not function as a
way to gather or group related BCs."

The data agrees independently. Categories are shared and connect concepts;
synonyms are 2,866 uses over 2,839 distinct values with only **23** shared by more
than one concept. So synonyms are correctly literals, and categories are not.

**Direction, not yet implemented** (decision D18): a category becomes an
unresolved label-node in the core rendering — the published token, asserting
nothing beyond its existence and which concepts carry it — while resolving a token
to the concept it names is an authored join and belongs to the overlay layer.

Note the consequence when it lands: the published shape types `categories` as
`sh:datatype xsd:string` with `sh:nodeKind sh:Literal`, so nodes will add a fifth
cause to the conformance report in §7d. It is the sharpest of them — CDISC's
article says `categories` is how related concepts are gathered, and CDISC's
published constraint says it is a string.

## 8. This repo — what is claimed about LOINC and NCIt, and what is not

Two claims are made, both verified before use.

**NCIt.** A concept's subject IRI is its OBO PURL (decision D2). The evidence for
that form — the EVS host being NXDOMAIN, NCI Thesaurus still declaring the
namespace, the OBO PURL resolving — is `usdm-rdf` decision D4 and is not
re-established here.

**LOINC.** A coding's IRI is `system` + `code` composed (decision D10).
`https://loinc.org/64098-7` was confirmed in a browser to resolve to "Six minute
walk test", status Active, 2026-09-01. A `curl` check returns 403, a bot block,
which proves nothing either way.

**What is deliberately not claimed:** any mapping relation between a biomedical
concept and its LOINC term. No `skos:exactMatch`, `narrowMatch` or `broadMatch` is
emitted. The coding node is the LOINC term; what it means relative to the concept
is unstated, because it is often not equivalence — see decision D10.
