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

## 4a. Upstream — the result-scale enum mixes two axes

`BiomedicalConceptResultScaleEnum` has five permissible values: `Nominal`,
`Ordinal`, `Quantitative`, `Narrative`, `Temporal`. None carries a `meaning:`
(decision D20). Read as terminology, they are not one axis: Nominal and Ordinal
are scales of measurement, and NCIt has both under its Scale branch (`C47798`,
`C47797`); Quantitative is a class of scales — Interval and Ratio together — with
no concept of its own; Narrative (`C80446`) and Temporal (`C73990`) are kinds of
value, not scales, and NCIt's own `Result Scale` concept `C227331` defines four
values and omits Temporal.

**The pinned export says the same thing independently.** Cross-tabulating each
single-scale concept's `result_scales` against the `data_type` of its Observation
Result data element concept (`C70856`), at commit `031429b1`:

| `result_scales` | concepts | Observation Result `data_type` |
|---|---|---|
| `Quantitative` | 390 | decimal 285, integer 51, float 2, string 15 |
| `Nominal` | 334 | string 162, integer 1 |
| `Ordinal` | 327 | string 48, boolean 4, decimal 1 |
| **`Temporal`** | **29** | **datetime 12, duration 1, decimal 3** |
| **`Narrative`** | **8** | **string 7** |

(The remainder in each row have no `C70856`. The three `Temporal` decimals are
Disease-Free, Overall and Progression-free Survival — time-to-event in days,
a duration by another name.)

So `Temporal` and `Narrative` are predicted by the result data type: they say what
kind of value the result is, which is exactly what `DataElementConceptDataTypeEnum`
already says with `datetime`, `date`, `duration` and `string`. The three genuine
scales are not predicted by data type — `Ordinal` results are strings, booleans
and decimals — because a scale is a different thing from a type.

**The combinations agree.** 91 concepts carry more than one scale: `Ordinal;
Quantitative` 51 times, `Nominal;Quantitative` 13, `Nominal;Ordinal` 12. `Temporal`
combines with nothing — 29 of 29 single-valued. The real scales combine because a
concept can be reported on more than one; a data type does not combine with a
scale because it is not one.

**Why this repo cares.** The overlay's identity rule for a qualified concept is
component × system × scale, with `resultScale` single-valued — the sibling split
axis (`overlay/qbc.schema.yaml`, header rule 1, and decision D20). That rule needs
scale to be one axis. If two of the five values are data types, they belong on the
result data element concept's `dataType`, which the overlay already treats as
authoritative, and the scale enum reduces to three values that anchor cleanly to
NCIt's Scale branch. The question was put to the DDS maintainer on 2026-09-01: is
result scale meant to be one axis or two?

**Meanwhile, the overlay works under the one-axis reading — decision D23.** Three
`qbc:ResultScale` nodes, one per real scale, anchored to NCIt's Scale branch on
the overlay's own nodes; Temporal and Narrative get none, and a qualified concept
may use only the three. The core rendering of the enum is untouched, and the
decision entry sizes what changes under either answer.

## 4b. Upstream — what NCIt already holds for the two bare BC enums

Verified 2026-09-02 against the NCI EVS REST API (NCIt 26.07d, public, no key:
`https://api-evsrest.nci.nih.gov/api/v1/`). Recorded so that the ask in §4 and
§4a can be sized: how much would have to be created, and how much already exists.

**No CDISC data-type codelist exists.** `C165634 CDISC Define-XML Terminology` has
fifteen child subsets — origin type and source, standard name/type/status, ODM
context, the ADaM subclasses, analysis purpose and reason — and none is a data
type. ODM and Define-XML data types have always been XML Schema enumerations, not
controlled terminology. The one CDISC-sourced concept in the area, `C201319
Biomedical Concept Property Response Data Type`, is an *attribute name* (a member
of `C201256`, and a child of `C42645 Data Type`) with no value set behind it. So a
value set for `DataElementConceptDataTypeEnum` would be new, not a binding to
something existing.

**But `C42645 Data Type` has 118 children — the ISO 21090 / HL7 data types — and
they cover most of the nine values:**

| `DataElementConceptDataTypeEnum` | existing NCIt concept | |
|---|---|---|
| `boolean` | `C45254` Boolean | reuse |
| `string` | `C45253` String, or `C95818` Character String Data Type | reuse, one to choose |
| `integer` | `C95821` Integer Data Type | reuse |
| `float` | `C48150` Float | reuse |
| `date` | `C48871` Date Data Type | reuse |
| `datetime` | `C54086` Timestamp Data Type, or `C95678` Point in Time Date and Time Data Type | one to choose |
| `decimal` | `C95826` Real Data Type, or `C48870` Double | no "Decimal" concept exists |
| `uri` | `C95829` URL Data Type | URL is narrower than URI |
| `duration` | — | nothing; a new concept |

**For `BiomedicalConceptResultScaleEnum`**, per §4a: `C47798 Nominal Scale` and
`C47797 Ordinal Scale` exist under `C25664 Scale`; Quantitative needs one new
concept parenting `C47799 Interval Scale` and `C47800 Ratio Scale`; `C227331
Result Scale` exists as the natural subset name but its definition lists narrative
among the scales and omits temporal; Temporal and Narrative have no scale concept
because they are not scales.

**What that sizes the ask to.** Two subsets — one under `C227331`, one under
`C201319` — reusing eight existing data-type concepts and the two scale concepts,
choosing between candidates for three (`string`, `datetime`, `decimal`), accepting
one approximation (`uri`), and minting two (`duration`, a quantitative scale). Then, on the COSMoS side, the
`meaning:` line per value and `code_set` per enum that `OriginTypeEnum` already
demonstrates. That is a new-term request, not a modelling discussion — and it is
the same shape as the two enums CDISC has already anchored.

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

## 7. This repo — what the Dataset Specialization A-Box normalises, carries as-is, and does not yet do

The layer decision D4 deferred is rendered since 2026-09-06 —
`dss/cosmos_sdtm_v1.{DOMAIN}.instances.ttl`, 32 files, decisions D26–D32,
`52_render_dss.ipynb`. It is a mechanical rendering of the export, and these
are the places where that is not quite literally true, or where the export
itself is not consistent.

**Two normalisations at render time** (decision D32). `length` and
`significant_digits` arrive as decimals (`200.0`) where the model says integer;
they are cast, and the notebook stops if one is ever not integral.
`packageType` is not in the export at all and is set to the enum's single value,
as `50_` does for the concept layer. Both are stated in every file's header.

**One dependency on the export that is not a value.** The order of `variables`
is the export's row order (decision D5); it is carried as `rdf:_n` membership
(D27) and stated in every file's header. There is no other source for it.

**Five published references resolve to nothing.** Four specializations
(`QS.PATCHSURVEY*`) reference `NEW_` concepts and one variable
(`MI.SURGMARGSTATBREAST.MILOCDTL`) references `NEW_DEC1`; none has an NCIt code,
so under decision D2 there is no node to point at. The published string is
carried as a literal on the same property (D31) — the term type is the marker,
nothing is minted to flag it — and `reports/dss_unresolved_references.csv`
lists them. This is the D2 gap (§7b) seen from the other side.

**Upstream — 68 relationship objects name a variable outside their own
specialization.** Ten distinct names (`TSVALCD`, `SUDECOD`, `RSLNKGRP`, …).
Rendered verbatim as literals (D30), no edge derived;
`reports/dss_unresolved_relationship_objects.csv` is the list, and it is
curator input rather than a rendering defect.

**Schema-permitted, and not gaps.** 476 assigned terms carry a value and no
concept (`conceptId` is optional); seven variables carry no `role` (optional).
Counted in the notebook, not reported.

**`subsetCodelist` is a label, rendered as one.** 296 variables carry it, under
26 distinct names (`NY_NY` and the like), always beside a `valueList` on a
codelist-bound variable. It is a literal here because nothing published gives it
an identity, and the export behaves accordingly: measured in `cdisc-for-ai`
([Link_Semantics.md](https://github.com/kerfors/cdisc-for-ai/blob/main/link-semantics/docs/Link_Semantics.md)), no name is used for two different (codelist, value list)
combinations and no combination carries two names, but most combinations are
never named at all. Consistent where applied, not an identifier.

**Not yet done for this layer.** The `dss/` w3id segment is reserved and not
registered, so nothing under it dereferences yet; the eight overlay recordings
(D17) are no longer dangling but `75_` has not re-measured it. Per-individual
HTML is not rendered for any layer. The phases in `README.md` say what is
intended; nothing there is a promise.

The overlay is rendered — `cosmos_qbc_v1.ttl` and `cosmos_qbc_v1.instances.ttl`,
decisions D13–D21 — and frozen in scope by decision D25.

**The core term IRIs do not dereference.** The w3id namespace is registered
(P5), so `https://w3id.org/cdisc/cosmos/bc/` and everything this repo mints under
it resolve. The class and property IRIs of the core rendering do not: they are
CDISC's published strings, and both schema ids return 404 on `cdisc.org` (checked
2026-09-01, with `https://www.cdisc.org/cosmos/` redirecting to a page slugged
`cdisc-biomedical-concepts-old`). That half is not this repo's to fix — see
decision D7.

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

41,620 violations, six causes, every one classified by
`60_validate_instances.ipynb` and recorded in `reports/shacl_conformance.csv`. The
full argument is decision D11. In short: `sh:closed true` rejects the identity
triples the schema has no slot for; `gen-owl` and `gen-shacl` disagree about
whether an enum value is a class IRI or a string; `parentConceptId` and
`categories` are typed `string`, so rendering either as an edge is an error by the
model's own rules; and the shape requires exactly one `dataType` on a data element
concept that has up to seven (§7f, decisions D18 and D21).

Not a defect to fix. Conforming would mean parent references stay strings and the
NCIt anchoring leaves the data.

**The Dataset Specialization layer, same stance, tighter check.** 117,424
results over the 32 domain files, five causes, every one classified by
`62_validate_dss_instances.ipynb` and summarised in
`reports/dss_shacl_conformance_summary.csv`. The notebook goes one step further
than `60_`: each cause's count is predicted from the data graph and asserted
equal, per domain, so a violation is accounted for exactly rather than
explained. The causes are the `rdf:_n` order on the closed `SDTMGroup` shape
(D27, not patched — see the amendment there), the two identity triples (D3,
D29), the enum disagreement, and the three `*ConceptId` references rendered as
edges (D21, D28, D31); the five references carried as literals (§7) conform.

One measurement falls out of it. The enum disagreement hits six enums and not
`OriginTypeEnum` or `OriginSourceEnum`: those two carry `meaning:` in the
published model, so both generators emit the NCIt IRI and the rendering
conforms. The same rendering, on the same package, passes where the model is
anchored and fails where it is not — which is the §4b ask, measured.

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

The nineteen are the whole same-node population inside this repo. Measured on
the v0.4.0 graphs: in the concept A-Box 1,450 NCIt IRIs are subjects as a BC
only, 205 as a DEC only, 19 as both; in the Dataset Specialization A-Box the only
NCIt subjects are the 297 codelist nodes, and none of them is also a BC or DEC
node. The same IRI does appear in object position under another role — 1,004 BC
or DEC nodes are also the `conceptId` of an assigned term somewhere — but
`conceptId` says nothing about the identity of the variable that carries it, so
no two subjects become one. Under decision D2 a code is one node whatever role
it plays; that only turns into a merge where the roles are both subject-side,
and here that is the nineteen. The wider population — every C-code used in more
than one role across the COSMoS export, SDTM CT and the test-code extracts — is
measured in `cdisc-for-ai` ([Link_Semantics.md](https://github.com/kerfors/cdisc-for-ai/blob/main/link-semantics/docs/Link_Semantics.md)); most of those roles are not rendered
here.

## 7f. This repo — `categories` was rendered as literals, and that dropped a grouping mechanism

Until 2026-09-02, `cosmos_bc_v1.instances.ttl` emitted `categories` as **4,389
string literals over 408 distinct tokens** — `QRS` carried by 291 concepts,
`Laboratory Tests` by 186, 104 tokens used exactly once. So the attribute that
connects concepts to one another was flat text, and the BC layer could not be
traversed by classification.

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

**Implemented 2026-09-02** (decision D18): a category is an unresolved label-node
in the core rendering — the published token, asserting nothing beyond its
existence and which concepts carry it — while resolving a token to the concept it
names is an authored join and belongs to the overlay layer. 405 nodes, 4,366
edges.

The published shape types `categories` as `sh:datatype xsd:string` with
`sh:nodeKind sh:Literal`, so the nodes add a cause to the conformance report in
§7d. It is the sharpest of them — CDISC's article says `categories` is how related
concepts are gathered, and CDISC's published constraint says it is a string.

The same re-render corrected a defect of this repo's own: `dataType` and
`exampleSet` were rendered once per data element concept, when at this pin they
vary by (concept, DEC) pair — decision D21.

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

**LOINC is rendered at two grains, and only one of them is an IRI.** The
concept-level `coding` (104 concepts, 97 coding nodes) composes `system` + `code`
into an IRI under D10. The specialization-level `--LOINC` variables do not: 98
carry the code as the `value` literal of an assigned term, 42 carry several codes
as `valueList` literals, 11 carry nothing — 140 specializations in all. The export
gives no `system` at that grain; that a `--LOINC` value is a LOINC code follows
from the variable name, which is a reading, not a published field, so the literal
is the mechanical rendering. A consumer asking for everything LOINC therefore
finds the 104 concepts and not the 140 specializations unless it also reads the
variable names. In this package the two grains never disagree: 11 specializations
sit on a concept that has its own coding, and in all 11 the concept's code is
among the specialization's. What the multi-code lists assert is measured in
`cdisc-for-ai` ([Link_Semantics.md](https://github.com/kerfors/cdisc-for-ai/blob/main/link-semantics/docs/Link_Semantics.md)).

**Link kinds, seen from outside.** Every relation this rendering emits between a
model element and an NCIt or LOINC term uses the published schema's own slot —
`conceptId`, `dataElementConceptId`, `codelist`, `parentConceptId`, `coding` — or
is the subject IRI itself (D2). None of them is a SKOS mapping property, and none
is transitive or symmetric, so merging these graphs with `usdm-rdf` or with NCIt
creates no equivalence that the sources do not state. The only `skos:exactMatch`
in the core graphs links the OBO and EVS forms of one concept. This is a
consequence of rendering the schema mechanically (D25), not a separate decision;
the audit that classifies the link kinds is in `cdisc-for-ai` ([Link_Semantics.md](https://github.com/kerfors/cdisc-for-ai/blob/main/link-semantics/docs/Link_Semantics.md)).
