# Decisions

Numbered decisions for this repo, in the style of `usdm-rdf`
`docs/iri-and-governance.md` (D1–D6 there). Each is an argument, not a code
change; a decision moves from OPEN to SETTLED only when it has been acted on.

D1–D21 are settled. D5 is settled but not yet exercised, since the layer it
governs is deferred; D3 is exercised by the overlay (see D17). D18 and D21 were
implemented together in one re-render of the core A-Box on 2026-09-02, so there
is one set of baselines rather than two.

---

## D1 — One core graph or two SETTLED 2026-09-01: two graphs

**Question.** Publish one merged core rendering of COSMoS, or two —
`cosmos_bc_v1.ttl` and `cosmos_sdtm_v1.ttl`?

**Settled: two graphs.** Not on the argument sketched below but on a test — the
merged option does not work, and the specific fix the kickoff brief proposed
(explicit `slot_uri` on the six colliding names) makes it worse rather than
better.

**Method.** linkml 1.11.1, against the two models at the pinned commit
`031429b1`. Probe run outside the repo; no repo code depends on it.

### Two graphs — works completely, no new code

| Generator | `cosmos_bc_model.yaml` | `cosmos_sdtm_model.yaml` |
|---|---|---|
| `gen-owl` | 19,773 bytes, 512 triples | 102,162 bytes, 2,005 triples |
| `gen-shacl` | 6,985 bytes | 18,504 bytes |
| `gen-jsonld-context` | 2,443 bytes | 5,139 bytes |

Classes: BC 6 top-level plus 15 enum permissible values; SDTM 24 top-level plus
146 permissible values. Nine of the SDTM top-level classes are `NCIT_*` — the
Define-XML origin terms, emitted as classes from their enum `meaning:` values.
Note that the bulk of the "class" count is enum permissible values, not concepts.

### Merged — does not work

**Plain merge** (imports both published models, `cosmos_bc_model` last per the
known import-order gotcha):

- `gen-owl` succeeds — 119,255 bytes.
- `gen-jsonld-context` fails, same error as 2026-08-30:
  `Conflicting URIs (…/biomedical_concept_v1.0, …/sdtm_v1.0) for item: conceptId`.
- Worse than the failure: where it *succeeds*, it loses meaning silently. All six
  colliding slots resolve to the **BC** definition. Read back through
  `SchemaView`, the merged schema says:

  | Slot | Merged value | SDTM value that was deleted |
  |---|---|---|
  | `conceptId` | pattern `^(C[0-9]+\|NEW_[A-Z_]*[0-9]*)$`, "an identifier that uniquely represents an entity" | pattern `^(C[0-9]+\|CNEW)$`, "C-code for a codelist in NCIt" |
  | `dataType` | `DataElementConceptDataTypeEnum` (9 values) | `SDTMVariableDataTypeEnum` (5 values) |

  So in the merged schema a `CodeList.conceptId` of `CNEW` fails validation and
  one of `NEW_FOO` wrongly passes. This is not an enum swap; it is the SDTM
  meaning being deleted without a diagnostic.

**Merge with explicit `slot_uri` on the six** — the brief's proposed fix:

- `gen-owl` succeeds (111,830 bytes), `gen-shacl` succeeds (24,094 bytes).
- `gen-jsonld-context` **still fails**. The conflict moves rather than resolves:
  `Conflicting URIs (…/sdtm_v1.0, https://w3id.org/cdisc/cosmos/core) for item: packageDate`.
- And declaring a slot in order to attach `slot_uri` **replaces** the imported
  definition rather than annotating it. After the override, `conceptId` and
  `dataType` both read back as `pattern=None, range=None`. Both meanings are now
  gone, not one.

### Why `slot_uri` cannot work, in principle

A slot name is a dictionary key. One merged schema holds exactly one `conceptId`.
So a merge collapses six pairs of semantically different slots into six single
slots no matter what URI is attached afterwards. Genuine disambiguation needs
**renaming** — `bcConceptId` / `sdtmConceptId` — inside vendored, patched copies
of the published models. That changes the slot names a consumer reads in the
published standard, which is a much larger authored act than the brief assumed,
and it fails the layering test outright.

### Consequence for D2 and P2

The 2026-08-30 finding that `gen-jsonld-context` is blocked was measured on a
schema that imports both models. Per schema it is **not** blocked: both contexts
generate. So the context blocker is a **merge** blocker, not a per-schema one,
and P2 is not gated on it. What P2 is still gated on is the bare C-code with no
prefix binding — D2, unchanged.

### What two graphs costs

The consumer imports two graphs, and the BC and DSS layers share no term IRIs.
The BC-to-DSS join therefore lives in the A-Box, on the `bc_id` /
`biomedicalConceptId` value, exactly as it does in the published exports. That is
the honest rendering of what CDISC publishes: two schemas, two namespace ids, one
join key.

---

## D2 — Identity binding for concept codes SETTLED 2026-09-01

**Question.** How does a bare C-code in the export become a subject IRI?

**Settled.** The subject IRI of a concept is its **NCIt OBO PURL**,
`http://purl.obolibrary.org/obo/NCIT_C115805`, with `skos:exactMatch` to the EVS
identifier so `usdm-rdf` decision D4's "always both" rule holds. **Concepts with
no NCIt code are not rendered.** This repo mints no identifier for them.

**Measured first.** Across the pinned export, `bc_id` equals `ncit_code` in all
6,283 rows where both are present, and `dec_id` equals `ncit_dec_code` in all
6,027. The `ncit_code` column is not additional information; it is `bc_id` again
whenever `bc_id` is an NCIt code. So **1,469 of 1,475** biomedical concepts arrive
with a resolvable identifier and need nothing invented.

**The six that do not** — recorded in `reports/unidentified_concepts.csv` by
`45_identity_probe.ipynb`, not asserted here:

| id | label |
|---|---|
| `NEW_1` | Urine Glucose Test Strip Measurement [RETIRED] |
| `NEW_LZZT` | TTS Acceptability Survey |
| `NEW_LZZT1`–`NEW_LZZT4` | TTS Acceptability Survey — Patch Appearance / Size / Durability / Acceptability |

Plus two data element concepts, `NEW_DEC1` (Specimen Location Detail) and
`NEW_DEC2` (Specimen Condition).

**Why not render them.** Every alternative requires this repo to name something
CDISC did not, which is what decision D7 declined to do at the ontology level and
what the layering rule excludes from core. A minted IRI for a placeholder is an
assertion that the concept has an identity; it does not.

**The cost, stated rather than mitigated away.** A consumer cannot tell a
deliberate gap from an oversight by reading the graph. So the gap is recorded
outside it: `reports/unidentified_concepts.csv` names all eight, derived from the
pinned export on every run. A blank node — present, typed, with no identifier —
was considered as a way of saying "this concept exists and cannot be named", and
not taken; rendering it as absent keeps the core strictly derived.

**Known consequence for P3.** Four DSSs in domain QS
(`PATCHSURVEYACCEPTABILITY`, `PATCHSURVEYAPPEARANCE`, `PATCHSURVEYDURABILITY`,
`PATCHSURVEYSIZE`, 32 rows) reference `NEW_LZZT1`–`4`, and one
(`SURGMARGSTATBREAST`) references `NEW_DEC1`. Their `biomedicalConceptId` link
will have no target. P3 must decide whether to omit the link or carry the
placeholder as a literal; either way the report above is what explains it.

### What the probe measured

`45_identity_probe.ipynb` runs five attempts against real rows and asserts each
outcome, so the notebook fails if the published schema changes:

| # | Schema | Instance | Result |
|---|---|---|---|
| 1 | as published | bare C-code | `ValueError: Unknown CURIE prefix: @base` |
| 2 | `+ id_prefixes: [NCIT]` | bare C-code | same — `id_prefixes` constrains prefixes, it does not expand a bare string |
| 3 | as published | `NCIT:`-lifted | **validation** fails: `'NCIT:C91106' does not match '^(C[0-9]+\|NEW_...)$'` |
| 4 | relaxed pattern, `range: uriorcurie` | `NCIT:`-lifted | converts; subject `obo:NCIT_C115805`, DEC references become graph links |
| 5 | same as 4 | `NEW_LZZT1` | fails — no prefix exists, and none can |

**The finding that matters is attempt 3.** The published pattern
`^(C[0-9]+|NEW_[A-Z_]*[0-9]*)$` forbids the only form that converts. An instance
can be schema-valid or RDF-convertible, not both, as published. That is not a
missing binding — it is a constraint actively ruling identity out, and it is the
argument to CDISC.

**Attempt 5 is the qualified-BC thesis as a stack trace**: a concept that
validates perfectly and cannot be named, inside the CDISC pilot study's own
instrument.

Two smaller observations from attempt 4: the LOINC `coding` converts to a **blank
node** — `code` + `system` are present but nothing composes them into an IRI; and
`ncitCode` becomes a literal duplicate of the subject IRI, since the two columns
are equal wherever both exist.

---

## D3 — DSS identity SETTLED 2026-09-01

**Question.** What is the subject IRI of a Dataset Specialization?

**Settled.** Domain-scoped under this repo's namespace —
`https://w3id.org/cdisc/cosmos/dss/{DOMAIN}/{MNEMONIC}`, e.g.
`.../dss/LB/GLUCSER` — with `datasetSpecializationId` carried as
`dcterms:identifier`.

**This does not contradict D7.** D7 declined to *rename* things CDISC named. Here
CDISC named nothing: `datasetSpecializationId` is declared `identifier: true` but
its pattern `^[A-Z][A-Z0-9_]*$` enforces only an uppercase mnemonic. Minting is
unavoidable; the question was only under which namespace and at what scope.

**Why domain-scoped.** Measured at this pin, 0 of 1,475 mnemonics appear in more
than one domain, so a flat IRI would work today. Nothing in the standard
guarantees it, and a future collision would silently merge two different
specializations onto one IRI. The scoping costs nothing and removes that failure
mode.

**Now exercised, by the overlay rather than by the layer it was written for.**
Decision D4 still defers the Dataset Specialization A-Box, so no specialization is
rendered — but decision D17 makes a recording's subject the Dataset Specialization
IRI, so eight IRIs in this scheme are minted in `cosmos_qbc_v1.instances.ttl` and
carry no other triples until that layer lands.

---

## D4 — A-Box scope SETTLED 2026-09-01: the BC layer

**Question.** Render the full package, or a subset first?

**Settled: the Biomedical Concept layer in full; the Dataset Specialization layer
deferred.** `cosmos_bc_v1.instances.ttl` carries 1,469 concepts, 224 data element
concepts, 97 codings and 1,166 parent edges — 29,697 triples.

**Why this cut rather than a sample.** The BC layer is where identity is settled
and where the NCIt anchoring pays off, and it is small enough to commit and read.
The DSS layer is where the volume is — 13,922 variables and roughly 450,000
triples — and where D3 and D5 would first be exercised. Rendering the whole
package at once would mean getting every decision right at full scale on the first
attempt, with a 25–40 MB artifact in git.

**Not rendered:** the six concepts with no NCIt code (D2), and their two data
element concepts `NEW_DEC1` and `NEW_DEC2`. The 105th LOINC coding goes with them,
since it belongs to `NEW_1`.

---

## D5 — Row-order dependency SETTLED 2026-09-01

**Question.** May `variables` ordering rely on CSV row order?

**Settled: yes, with an explicit index and the dependency stated in the
deliverable's provenance.** No alternative survived measurement.

**What was measured.** The DSS model requires an *ordered* `variables` list; the
export has no order column. Order cannot be reconstructed from any per-variable
rule: **225 of 458 variables appear at more than one position** across DSSs, so
position is a property of the specialization rather than of the variable. The
first variable is the domain's `TESTCD` in almost every DSS — the SDTM convention
— but that fixes position 1 and nothing beyond it.

So the choice was between relying on row order and dropping order altogether, and
dropping it contradicts a required property of the published model. Relying on it
is derived; what must not happen is relying on it silently.

**Two related measurements, both clean at this pin.** Every DSS-level column is
constant within its group (maximum 1 distinct value across all seven), so the DSS
node rebuilds by grouping. And `(DSS, variable)` is unique — 13,922 pairs, zero
repeats — so each row is exactly one `SDTMVariable`, with no VLM duplication to
resolve.

**Not yet exercised** — D4 defers the layer this governs.

---

## D6 — Where repairs to the source live SETTLED 2026-09-01

**Question.** `cosmos_bc_model.yaml` has a defect that must be repaired before it
renders (`known-gaps.md` §1a). Where does the repair live?

**Settled.** `downloads/` holds upstream bytes verbatim — it is what the SHA-256
sidecars describe, and editing it would make the checksums lie.
`20_generate.ipynb` applies the repair to a copy in `build/` (gitignored,
derived) and **writes `patches/cosmos_bc_prefix.patch` as an output**, so the
committed patch cannot drift from what was actually applied. The substitution is
asserted to match exactly once: if upstream fixes the defect, generation fails
loudly rather than silently doing nothing, which is the correct signal to drop
the repair.

**Also settled here: every generator option is passed explicitly.**
`OwlSchemaGenerator`'s Python defaults are not the `gen-owl` CLI defaults — the
class defaults to `metaclasses=True` and `type_objects=True`, which the CLI turns
off. Measured 2026-09-01: constructing with class defaults gives 551 triples
instead of 512 for the BC model and emits **every** datatype property as an
`owl:ObjectProperty` (13 becomes 0). The result parses, validates and looks like
an ontology, and is wrong. The pinned option set reproduces the CLI output
triple-for-triple, so a future diff means a source change rather than a toolchain
change. For a repo whose thesis is "the constraints were already published, just
generate them", a generator whose API and CLI disagree by default is worth naming
in the write-up.

---

## D7 — Ontology IRI of each deliverable SETTLED 2026-09-01: option A

**Question.** What names the ontology, and does that name reach the terms?

**Settled: the ontology is named under w3id, the terms are not.**

| | `cosmos_bc_v1.ttl` | `cosmos_sdtm_v1.ttl` |
|---|---|---|
| ontology IRI | `https://w3id.org/cdisc/cosmos/bc/` | `https://w3id.org/cdisc/cosmos/sdtm/` |
| `owl:versionIRI` | `…/cosmos/bc/0.1.0` | `…/cosmos/sdtm/0.1.0` |
| term namespace | `https://www.cdisc.org/cosmos/biomedical_concept_v1.0/` | `https://www.cdisc.org/cosmos/sdtm_v1.0/` |

**How the question arose.** Left alone, the generator's `ontology_uri_suffix`
default would have named the ontology
`https://www.cdisc.org/cosmos/biomedical_concept_v1.0.owl.ttl` — a file name
standing in for an ontology IRI, settled by a default nobody looked at.

**The options weighed.** (A) name the ontology under w3id, leave term IRIs as
published. (B) full `usdm-rdf` parity — mint term IRIs under w3id too, with
`skos:exactMatch` back to the published ones. (C) keep CDISC's term IRIs canonical
and additionally assert w3id aliases.

**Why A.** B was free for `usdm-rdf` because `dataStructure.yml` declares no
namespace at all — there was nothing to displace. Here both models declare
prefixes, so B means this rendering renames every term CDISC published: the BC
patch would grow from a one-character repair into a namespace rewrite, the core
layer would stop being a mechanical rendering, and the artifact would be harder to
hand to CDISC, since accepting it would mean accepting new names for their own
terms. C gives every term two IRIs and no stated canonical one — the exact
ambiguity the qualified-BC work exists to remove.

A buys the parts of the `usdm-rdf` shape that cost nothing: a real ontology IRI, a
version-pinned release IRI, a citable header, one w3id PR. It renames nothing.

**What A does not buy, stated plainly.** Term IRIs will not dereference. They are
CDISC's strings on a host that returns 404 for both schema ids (checked
2026-09-01). That is CDISC's namespace to fix, not this repo's — and it is worth
noticing that CDISC's declared ids are IRI-shaped names rather than working
identifiers, which is the qualified-BC argument one layer up from the bare
C-code.

**What is preserved.** CDISC's declared schema id survives where it matters — as
the namespace every term IRI still sits in — and is advertised explicitly as
`vann:preferredNamespaceUri`. The ontology IRI and the term namespace therefore
differ. That is the decision, not an oversight, and `30_validate.ipynb` guards it:
the only IRIs permitted in the w3id namespace are the ontology and its version.

**Carried over from `usdm-rdf` with this decision:** bare-numeric `versionIRI`
in-namespace (their D3), so one generic w3id rewrite rule dereferences every
release including past ones; `dcterms:created` fixed at first publication and
never advancing, with `dcterms:modified` tracking the release (their D1); and
every annotation predicate declared `owl:AnnotationProperty` so derived
serializations add no declarations the canonical graph lacks (their D2).

**Still open at P5:** the `.htaccess` rule set, and whether the two segments sit
under one w3id registration or two. One registration of `/cdisc/cosmos/` covering
both segments plus the DDS profile id is the assumption.

---

## D8 — How instances become RDF SETTLED 2026-09-01

**Question.** Does the A-Box go through `linkml-convert`, or does this repo render
it directly?

**Settled: both, with different jobs.** P3 renders the A-Box directly from the
un-flattened CSV with `rdflib`, using the T-Box IRIs and minting subjects per D2.
The patched `linkml-convert` path is kept as a **comparison check** on a sample,
not as a build step.

**Why not `linkml-convert` alone.** It requires the repair set to grow from a
typo fix into an edit of a published *constraint* — relax the `conceptId` pattern,
change its range, and CURIE-lift every code at ingest — reapplied on every pin
bump. A patch that edits a constraint is a different kind of object from a patch
that adds a missing slash, and the difference should not blur.

**Why not the direct renderer alone.** The claim "the published pattern forbids
RDF" is worth more as a reproducible demonstration than as a sentence. Keeping
both paths turns it into one, and gives the renderer an independent check: where
both can run, they must agree.

**Consequence.** The A-Box is this repo's code rather than the generator's, so
conformance has to be shown rather than assumed — the SHACL shapes in P3 are what
show it, and they are generated from the published schema.

**Result, measured 2026-09-01.** `65_compare_render_paths.ipynb` runs both paths
over six concepts chosen by shape — coding, several DECs, no DECs, no parent,
multiple result scales, and one used at both layers — and compares every predicate
on the concept node. **44 comparisons agree, 32 differ, none unexplained.** The
agreements are the check working: `categories`, `definition`, `ncitCode`,
`packageDate`, `shortName`, `synonyms` and `dataElementConcepts` come out
identical from two independent implementations, with nothing tuned to make them
match.

Every difference falls into a cause already recorded — D2's authored identity
triples, D10's composed coding IRI, D11's enum and `parentConceptId` divergences,
D12's dual-role merge. The guard earned its place on the first run by catching two
D12 differences that had not been written down.

**And it says which side the third generator takes.** On enum values and on
`parentConceptId`, `linkml-convert` emits literals — agreeing with `gen-shacl` and
not with `gen-owl`. Of the three LinkML generators reading one published schema,
two produce a document-shaped reading and one a graph-shaped reading, and the
outlier is the one this repo's T-Box is generated from. That is worth stating
plainly in the write-up: the divergence is not this repo's interpretation, it is
already present inside the toolchain CDISC publishes for.

---

## D9 — Deliverables are canonicalized before serialization SETTLED 2026-09-01

**Question.** Should the Turtle output be canonicalized, or written as `rdflib`
serializes it?

**The problem, measured.** Re-running `20_generate.ipynb` with no input change
rewrote **292 lines across the two deliverables** while the graphs stayed
isomorphic — 535 and 2,028 triples both before and after. The cause is anonymous
nodes: 110 in the BC graph and 421 in the SDTM one, nearly all `owl:Restriction`
cardinality blocks, which `rdflib` relabels on every serialization.

**Why that is not cosmetic.** `README.md` promises that a deviation from a fresh
pin means a source change or a generation bug. With churning bytes it means
neither, and a reviewer learns to ignore the diff — which is the same failure as
the `generation_date` timestamp removed from the JSON-LD contexts, on the primary
artifact rather than a secondary one.

**Settled.** `20_generate.ipynb` passes each graph through
`rdflib.compare.to_canonical_graph()` before writing, which labels blank nodes
deterministically from graph structure. The notebook asserts that the canonical
graph is isomorphic to the generated one, that the triple count is unchanged, and
that a second canonicalization of the serialized output reproduces the same bytes.
Verified 2026-09-01: three consecutive runs produce identical checksums.

Two practical notes. `to_canonical_graph` returns a read-only aggregate, so the
triples are copied into a writable graph before prefixes are re-bound —
canonicalization drops prefix bindings, and without re-binding the output shows
`ns1:` in place of `linkml:`. And the switch is a one-time reflow of the committed
files: the canonical version is isomorphic to what was committed at P1, so no
content changed.

**Rejected.** Skolemizing the restrictions would also be stable, but it mints IRIs
for things CDISC did not name — the act decision D7 declined at the ontology
level. Sorting the serialized lines does not work at all, since the blank-node
identifiers themselves differ. Accepting the churn and weakening the README claim
was the honest fallback if canonicalization had made the file unreadable; it did
not.

---

## D10 — External code anchoring SETTLED 2026-09-01

**Question.** A concept's `coding` carries `code` and `system` but no IRI. Blank
node, or compose one?

**Settled: compose `system` + `code` into the coding's IRI.** The schema documents
`system` as "the URL of the code system", and the only system present is
`http://loinc.org/`, so `http://loinc.org/` + `64098-7` is derived from two
published fields rather than invented. All 98 distinct codes compose to
syntactically valid absolute IRIs.

**Verified, not assumed.** `https://loinc.org/64098-7` resolves to the LOINC term
"Six minute walk test", status Active — confirmed in a browser 2026-09-01. A
`curl` check returns 403, which is a bot block and proves nothing either way; the
repo's rule is that no LOINC claim goes in unverified, and this one is verified.

**What is deliberately *not* asserted.** No mapping predicate is emitted between a
biomedical concept and its LOINC term. The coding node *is* that term; what it
means relative to the concept is left unsaid, because it is frequently not
equivalence — the HCV RNA analysis in `cdisc-for-ai` found 16 `narrowMatch` and
one `broadMatch` and no `exactMatch` at all. `skos:exactMatch` here would be
precisely the unverified claim this repo refuses.

**Side effect, and it is the right one.** Seven codes are referenced by more than
one concept; identifying the coding by its IRI merges those onto one node, because
it is one LOINC term. The A-Box now contains **no blank nodes**.

---

## D11 — Where the published constraints and the RDF idiom disagree SETTLED 2026-09-01

**Question.** The A-Box does not conform to the SHACL generated from the published
schema. Adjust the graph, adjust the shapes, or report it?

**Settled: report it.** The shapes ship unmodified — they are CDISC's constraints,
not this repo's opinion of them — and the A-Box keeps the RDF idiom.
`60_validate_instances.ipynb` classifies every violation and **fails if one appears
that is not accounted for**.

**8,925 violations, four causes.**

| count | cause |
|---|---|
| 1,693 × 2 | `sh:closed true` rejects `skos:exactMatch` and `dcterms:identifier` — identity the schema has no slot for |
| 2,962 | `sh:in ("bc")` expects enum values as string literals; the OWL T-Box declares them as class IRIs |
| 1,166 × 2 | `parentConceptId` is `range: string`, so rendering the parent reference as a link violates datatype and node kind |
| ~230 | one node typed as both BC and DEC, each closed shape rejecting the other's slots (D12) |

**Why this is the finding and not a defect.** Three of the four are the same thing
seen three times: **the published constraints describe a document, not a graph.**
`gen-owl` and `gen-shacl`, from one schema, disagree about what an enum value even
is — one says class IRI, the other says string literal. And a parent reference
typed as a string means that turning it into an edge is, by the model's own rules,
an error. Conforming would mean parent references stay strings and the NCIt
anchoring disappears from the data: the graph would stop being a graph.

**Rejected.** Editing the shapes to admit the idiom would make conformance
circular. Authoring a second "graph profile" shapes graph, in the style of
`usdm-rdf`'s structural/terminology split, remains available if a consumer ever
needs something to validate against — but at P3 there is no such consumer, and the
divergence is more useful stated than smoothed over.

---

## D12 — Concepts used at two layers SETTLED 2026-09-01

**Question.** Nineteen NCIt codes are used as both a Biomedical Concept and a Data
Element Concept, so under D2 they resolve to one node carrying both types. Split
them, or accept the merge?

**Settled: accept the merge, and report the population rather than model around
it.** The same treatment the unidentified concepts get.

**The Demographics three are correct, not a compromise.** Race `C17049`, Sex
`C28421` and Ethnic Group `C16564` are each a BC with one DSS in DM and a DEC on
one DM variable — RACE, SEX, ETHNIC. The concept is the whole content of the
observation, so there is nothing for the two roles to be distinct from. Splitting
them would invent a distinction the data does not make.

**The rest are a mixed population, and the question is curation, not modelling.**
Fifteen have no DSS of their own as a BC; nine appear in no DSS in either role.
`C25330` Duration surfaces 48 times as a DEC in EG, `C82571` 24 times in BE and
DS. Whether a BC should exist that nothing specializes and that only ever appears
as a DEC is CDISC's call, not something this rendering should resolve.

Only **two** of the nineteen have labels that disagree — `C82571` "Reported Event
Term **[RETIRED]**" against "Reported Event Term", and `C83118` likewise. The
divergence is lifecycle annotation carried in the BC label and absent from the DEC
label, not two meanings. Those two produce the four `sh:maxCount` violations on
`shortName`.

All nineteen are recorded in `reports/dual_role_concepts.csv` with their DSS usage
on both sides, derived on every run.

---

## D13 — The namespace for qualified concepts SETTLED 2026-09-01

**Question.** A qualified concept has no CDISC identity — that is the point of it —
so minting is unavoidable and is not renaming. Under which namespace?

**Settled: `https://w3id.org/cdisc/cosmos/qbc/`**, and the overlay schema's own id
and default prefix move there with it. The draft carried
`id: https://w3id.org/cdisc/cosmos/sibling_bc_sketch_v0.1` and prefix `sbc:`; both
are gone.

**Why it had to move at all.** The draft minted concepts at
`https://w3id.org/cdisc/cosmos/bc/GlucoseBloodQuantitative` — inside the namespace
decision D7 made the **ontology IRI of the core BC graph**. Authored content sitting
in the namespace reserved for the mechanical rendering of the published standard is
precisely the core/overlay boundary this repo exists to keep. Fourteen instance IRIs
moved with the decision, ten in the glucose file and four in HCV RNA.

**Why `qbc` and not `sibling`.** "Sibling" is the working nickname; the class the
schema declares is `QualifiedBiomedicalConcept`. Naming the artifact after the
metaphor rather than the class would have to be explained every time.

**Why still under `/cdisc/`.** The alternative was a namespace of this repo's own,
which is cleaner on authorship and worse on everything else: it would make a later
transfer to CDISC an IRI change rather than a redirect change, and it would need its
own w3id registration. The schema header already states the intent — this is
demonstration authority, meant to transfer. Governance moves by changing the
redirect target, exactly as `iri-and-governance.md` describes.

**This is where decision D7 gets revisited, and the revisit is deliberate.** D7
option A holds that this repo names its ontologies and not CDISC's terms. The
overlay is the first deliverable that names **terms** under w3id — nine classes and
thirty-two properties. That is legitimate on the same grounds as the concepts: none
of them is CDISC's to rename, because CDISC never declared them. The argument
belongs in `iri-and-governance.md`, and the guard in `30_validate.ipynb` and
`scripts/ci_check.py` must admit the `qbc` segment **by name** rather than by
accident.

**One hazard the scheme creates, and the guard for it.** Concepts and classes share
one namespace, so a qualified concept named `Recording` would collide with the class
`Recording`. Measured at this pin: **zero collisions**, asserted on every run by
`75_render_qbc.ipynb`.

---

## D14 — How a qualified concept links to its broader concept SETTLED 2026-09-01: `skos:broader`

**Question.** The schema says `broaderConceptId: C105585`; the core A-Box already
renders `obo:NCIT_C105585` as a real node. Which predicate carries the relation?

**Settled: `skos:broader`. This decision was reversed mid-implementation, and the
reversal is the argument.**

**What was settled first, and why it looked right.** `skos:broadMatch`, on the
grounds that SKOS declares it `rdfs:subPropertyOf skos:broader`, so the weaker
statement follows by entailment and is never asserted twice — and on the grounds
that a mapping property is the honest reading when one concept is authored here and
the other is CDISC's.

**What rendering it showed.** Decision D16 asserts a mapping relation for every
authored external mapping, and HCV RNA maps to LOINC `111469-3` with relation
`broadMatch`. So one subject carried **eight `skos:broadMatch` triples — six analyte
links and two external mappings — distinguishable only by inspecting the target's
namespace.** A consumer asking what a concept is a specialization of would get a
LOINC order-term back. The entailment argument was correct and worth less than an
unambiguous graph.

**Settled therefore:** `skos:broader` for this repo's own concept hierarchy, the
`*Match` properties reserved for mappings out to external code systems. That is also
what `README.md` and `iri-and-governance.md` already promised in prose.

**Measured after the change.** Six `skos:broader` triples; all six targets are typed
`BiomedicalConcept` in `cosmos_bc_v1.instances.ttl`. Three `skos:exactMatch`,
twenty-three `skos:narrowMatch`, two `skos:broadMatch`, none of them landing on a
node the core graph describes.

**The guard has to test graph membership, not the target's host.** NCIt PURLs are
both this repo's identity scheme (D2) **and** a code system the overlay maps out to —
`GlucosePlasmaEquivalent` has an `exactMatch` to `obo:NCIT_C163446`. So
`purl.obolibrary.org` appears on both sides of the split, and a host-based check
gives a false failure. `75_render_qbc.ipynb` asserts that every `broader` target is
inside the core graph and no `*Match` target is.

**Also emitted, and it is not redundant.** `qbc:broaderConceptId` carries the same
link as an edge — the schema's own slot rendered graph-style, exactly as the core
A-Box renders `parentConceptId`, and violating the published shape in exactly the
same way (decision D11, third cause). `skos:broader` carries the meaning to a
consumer that has not read the schema; the slot carries what the schema says.

**The class-level `skos:broadMatch` stays.** `gen-owl` derives it from the schema's
`broad_mappings`, it is a statement about classes rather than instances, and it is
generated rather than authored. It is the machine-readable form of the own-class
decision: `QualifiedBiomedicalConcept` is not `is_a` `BiomedicalConcept`, it
broad-matches it.

---

## D15 — Interpretation regimes SETTLED 2026-09-01: the assertion without the pointer

**Question.** The schema declares `interpretationRegimes`, the one genuinely new
construct in the overlay. What is emitted?

**A correction first, because the decision turns on it.** The P4 hand-off note
recorded this slot as "declared and populated nowhere — 0 of 6 siblings". Measured
2026-09-01: **3 of 6 siblings, 5 assertions, 3 distinct regime URIs** — two on
blood-derived glucose, two on plasma-equivalent, one on urine categorical. Every one
carried `sourceAnchor: "[VERIFY] regime vocabulary does not exist; URI invented for
illustration"`.

So the question was never "is there anything to emit". It was "does an identifier
the author marked as invented go into a published deliverable".

**Settled: emit the assertion, omit the pointer.** The `regime` slot changes from
required to optional, and the five invented URIs are removed from the instance files
rather than carried and suppressed at render time — source and deliverable agree,
and nothing invented exists anywhere.

**What survives is still the ask.** An `InterpretationRegimeAssertion` renders with
its state data element concept, its state value and its source anchor. For glucose
that says: *a distinct interpretation regime applies when Fasting Status Indicator
C93566 is Y, and a different one when it is N.* What it cannot say is which. That is
precisely the governance gap — the regime vocabulary does not exist — and stating it
as a structured absence is worth more than three invented URIs that imply it does.

**Rejected: emit nothing.** It would have removed the overlay's only new construct,
and with it the reason the regime ask is legible at all.

**Rejected: emit the invented URIs with their `[VERIFY]` anchors.** Decision D2
declined to mint an identifier for a concept that has none, and rendered it absent
instead. Minting three here would make the repo's only fabricated identifiers the
ones it published most prominently.

**Guarded.** `75_render_qbc.ipynb` raises if any instance carries a `regime` value,
and asserts zero `qbc:regime` triples in the output. Five assertion nodes render.

---

## D16 — External mappings as real predicates SETTLED 2026-09-01

**Question.** `MappingRelationEnum` maps cleanly onto `skos:exactMatch` /
`narrowMatch` / `broadMatch`. Assert them, or keep the mapping reified and say
nothing about what it means?

**Settled: assert them, and keep the reified node as well.** Twenty-eight mappings
render as 3 `skos:exactMatch`, 23 `skos:narrowMatch` and 2 `skos:broadMatch`, each
alongside an `ExternalMapping` node carrying `code`, `system` and the comment.

**This is the one place the repo asserts a mapping relation, in deliberate contrast
to decision D10, and the contrast is the argument.** D10 refuses to emit any
predicate between a concept and its published COSMoS coding, because what the coding
means relative to the concept is frequently not equivalence and the package does not
say. Here the package is not the source: each relation was curated one at a time
against the LOINC service, is stated explicitly in the authored instance, and is
reviewable by anyone reading `overlay/*.instances.yaml`. Authored and inspectable may
assert; published and silent may not.

**Why both forms.** The SKOS triple is what makes the mapping queryable without
reading the schema. The reified node is what carries *why* — "mass concentration
(MCnc), Ser/Plas, Qn — unit axis" — which is the content that makes a `narrowMatch`
reviewable rather than merely typed. Neither is derivable from the other.

**The measurement that makes the case worth publishing.** HCV RNA carries nineteen
mappings and **not one `exactMatch`**: seventeen `narrowMatch` and two `broadMatch`,
because LOINC has no method-neutral leaf for the concept. A model in which a concept
has one code cannot hold that. A model in which the relation carries the cardinality
can.

**Where the line falls, and it is D10's line.** `externalMappings` composes an IRI
from `system` + `code` because the instance states a system. `loincPins` on a
recording states none — the system lives in the slot's name — so those stay
literals. Composing there would be an authored act the slot does not license.

---

## D17 — Recordings that point at Dataset Specializations SETTLED 2026-09-01

**Question.** Eight recordings reference DSS mnemonics. D3 settled the DSS IRI
scheme, but D4 deferred the DSS A-Box, so the targets do not exist. Link anyway, or
hold the recordings back?

**Settled: the recording's subject IS the Dataset Specialization IRI** —
`https://w3id.org/cdisc/cosmos/dss/{DOMAIN}/{MNEMONIC}`, typed `qbc:Recording`, with
the mnemonic as `dcterms:identifier`. Not a separate node pointing at one.

**Why identity rather than reference.** A recording and a dataset specialization are
the same specialization described at two grains: the overlay says what survives once
the qualified concept carries scale, specimen and result type; the DSS layer will say
the rest. Giving them one IRI means the two descriptions **merge on one node** when
that layer lands, rather than requiring a mapping between them to be maintained. The
thinness of a recording is a fact about which triples this graph asserts, not about
what the thing is.

**It also costs nothing to be wrong about.** D3 mints these IRIs under this repo's
own namespace; no external authority is being claimed, and nothing dereferences yet.

**Measured.** Eight recordings, all eight under the D3 namespace, and all eight with
no other triple in the graph — dangling by design while D4 defers the layer.
`75_render_qbc.ipynb` reports the count rather than hiding it, and asserts the IRI
form. When the DSS A-Box lands the number should go to zero, which makes it a
regression test for that phase.

**Rejected: a separate `qbc:recording/{ID}` node.** It needs a predicate to relate it
to the specialization, the schema declares none, and minting one would be authored
vocabulary invented to work around a self-inflicted split.

**Rejected: hold recordings back.** It would lose the inherit-once story — the result
data type living on the concept and not re-declared on the recording — which is half
of what the HCV RNA case demonstrates.

---

## D18 — `categories` as nodes SETTLED 2026-09-02

**Settled: a category is a label-node in core.** A concept's `categories` value
becomes an edge to `https://w3id.org/cdisc/cosmos/bc/category/{token}`, and that
node carries the token as `rdfs:label` and nothing else — no `rdf:type`, no claim
about what the token names. The resolution of a token to the concept it names is
authored, and belongs to the overlay. The token is published; the identity behind
it is inferred. Synonyms stay literals — measured, 2,866 synonym tokens of which
only 23 are shared by more than one concept, so making them nodes would add 2,839
nodes and almost no edges, where the category tokens are shared heavily.

**The slug rule.** The token, percent-encoded with nothing left unescaped. It is
exact and reversible, and `50_render_bc.ipynb` asserts the round-trip from label to
IRI on every run. Measured at this pin: 408 distinct tokens in the export, 33 of
them carrying a character outside letters, digits and space (`Tumor/Lesion
Results`, `Alzheimer's Disease Assessment Scale-Cognitive …`, `RECIST 1.1`), and no
two tokens differing only in case. **405** land on a rendered concept; `Surveys`,
`Acceptability Surveys` and `Questionnaires` occur only on the six concepts decision
D2 omits.

**This is the first time core mints an IRI under w3id**, and it is deliberate. D7
declined to rename anything CDISC named; a category token has no CDISC identity to
rename — it is an ungoverned string, see the caution below — so minting is not
renaming. Same ground as D13. The guard in `30_validate.ipynb` and
`scripts/ci_check.py` must admit the `category/` segment by name.

**Measured after the change.** 4,366 category edges to 405 nodes. Two new causes in
the conformance report, 4,366 each: the published shape types `categories` as
`sh:datatype xsd:string` with `sh:nodeKind sh:Literal`. Those are the sharpest of
the six — CDISC's own article says `categories` is how related concepts are
gathered, and CDISC's own constraint says it is a string.

See `known-gaps.md` §7f for what the deliverable did before this decision and why
it was a gap.

**A caution added 2026-09-01.** An earlier reading of NCIt held that CDISC publishes
a governed codelist for category values. It does not — see the verification
recorded under D20. `Biomedical Concept Category` (NCIt C201346) is a
CDISC-contributed **entity name** with no value set behind it, so the 408 tokens
are ungoverned strings. That makes the label-node treatment more
clearly right, not less: there is nothing upstream to resolve them against, and the
overlay's authored resolution is the only join available. The write-up must not claim
CDISC governs the values.

---

## D19 — The overlay schema's stand-ins for the SDTM import SETTLED 2026-09-01

**Question.** `sibling_bc.schema.yaml` imported both published models — exactly the
configuration decision D1 proved broken. What replaces it?

**Settled: the SDTM model is not imported. `AssignedTerm` and the `domain` slot are
declared locally, and the BC import is this repo's own patched copy.**

**Measured, as published.** `gen-owl` succeeds at 147,624 bytes; `gen-json-schema`
succeeds at 46,352 bytes, byte-identical to the JSON Schema committed in
`cdisc-for-ai`; `gen-jsonld-context` **fails** with
`Conflicting URIs (…/biomedical_concept_v1.0, …/sdtm_v1.0) for item: conceptId`; both
instance files validate.

**Measured, after dropping the import.** All four generators succeed, and both
instance files still validate — which is the check that is not vacuous: the BC
`dataType` enum still governs `float` / `string` / `boolean` on the data element
concepts, as the source repo's README notes it must.

**The two stand-ins are two lines of published content, copied verbatim** from
`cosmos_sdtm_model.yaml` at the pinned commit, with `class_uri` and `slot_uri`
pointing back at CDISC's term IRIs so nothing is renamed. Measured, and the two
generators disagree about whether that works: `gen-jsonld-context` honours both,
mapping `AssignedTerm` to `cosmos_sdtm:AssignedTerm` and `domain` to
`cosmos_sdtm:domain`. `gen-owl` mints `qbc:AssignedTerm` and demotes the published
IRI to a `skos:exactMatch`, and drops the `slot_uri` on `domain` **entirely**,
emitting `qbc:domain` with no mapping back. Both readings ship. The OWL one is
arguably the more honest — the stand-in *is* this repo's declaration, exact-matched
to CDISC's term, which is the core/overlay boundary stated in RDF.

**What dropping the import does not fix.** `linkml-convert` still fails, at
`conceptId: C70856` on the inherited data element concept —
`ValueError: Unknown CURIE prefix: @base`. That is decision D2 and `known-gaps.md`
§7a resurfacing through every published class the overlay reuses: the qualified
concept has resolvable identity, and the DEC it points at does not. **So there is no
`linkml-convert` comparison path for the overlay A-Box**, and decision D8's habit of
checking the direct renderer against the generator cannot be exercised here.

**A collision this decision introduces, left visible on purpose.** `conceptId`,
`value` and `sourceAnchor` are each declared on more than one class in the overlay
schema. LinkML collapses them onto one property IRI and `gen-owl` responds by
emitting a bare `owl:DatatypeProperty` with no range and no pattern, warning
`Ambiguous attribute` for each. `gen-shacl` keeps the per-class patterns apart —
`AssignedTerm.conceptId` `^(C[0-9]+|CNEW)$` against `ConceptTerm.conceptId`
`^(C[0-9]+)$`. Attaching `slot_uri` to the attributes silences the warning; measured,
that is all it does — the two attributes still resolve to one IRI and their
definitions are **merged** onto it rather than dropped. A loud collapse is worth more
than a quiet one, so the warning stays. This is decision D1's finding at overlay
scale, in a schema this repo wrote.

**Why the patched BC model, and it is not a preference.** The published model's
`cosmos_bc` prefix carries no separator (`known-gaps.md` §1a). Measured against the
unrepaired copy, the class-level `skos:broadMatch` resolves to
`https://www.cdisc.org/cosmos/biomedical_concept_v1.0BiomedicalConcept`, while the
core T-Box declares `…/biomedical_concept_v1.0/BiomedicalConcept`. **The one
machine-readable link the whole overlay hangs on landed in no graph.** Importing
`build/cosmos_bc_model.patched.yaml` fixes it, and fixes the self-containment
question at the same time. The consequence is an ordering constraint: the overlay
notebooks run after `10_fetch_cosmos.ipynb` and `20_generate.ipynb`.

---

## D20 — Enum values in the overlay SETTLED 2026-09-01

**Question.** A qualified concept's `resultScale` is a permissible value of an enum
CDISC published. Which IRI does the A-Box use, and what happens to the T-Box range?

**Settled: the A-Box resolves CDISC's enums out of the CORE T-Box**, so the overlay
shares those nodes with `cosmos_bc_v1.instances.ttl` —
`cosmos_bc:BiomedicalConceptResultScaleEnum#Quantitative`, not a value of this
repo's own. `MappingRelationEnum` is the overlay's, and resolves out of the overlay
T-Box. Both go through the same guard `50_render_bc.ipynb` uses: a value the
declaring T-Box does not have raises rather than being written.

**Why not mint the overlay's own.** It would give the same enum two IRIs, break the
join to core, and rename a term CDISC published — which is what D7 declined.

**The generator does not cooperate, and this is the finding.** `gen-owl` names an
imported enum after the **importing** schema, in either merge mode. With
`mergeimports` it redeclares three CDISC enums under `qbc:` —
`BiomedicalConceptResultScaleEnum`, `DataElementConceptDataTypeEnum`,
`PackageTypeEnum` — which is a D7 violation produced by a default. Hence
`mergeimports: False` in `70_generate_qbc.ipynb`, the only pinned option that differs
from `20_generate.ipynb`; unmerged, the overlay declares only its own nine classes.

**Unmerged still leaves a dangling reference, in two places.** `rdfs:range` on
`qbc:resultScale`, and `owl:allValuesFrom` inside the `owl:Restriction` on
`QualifiedBiomedicalConcept` — both naming `qbc:BiomedicalConceptResultScaleEnum`,
which is declared nowhere. A first repair that fixed only the range passed its own
check while the second pointer survived; the guard now looks at every object
position.

**Settled: retarget both to `cosmos_bc:BiomedicalConceptResultScaleEnum`**, which the
core T-Box already declares as `owl:unionOf` over exactly its five permissible
values. This is the idiom `usdm-rdf` uses for a multi-target range —
`rdfs:range [ a owl:Class ; owl:unionOf ( … ) ]`, with
`examples/05_polymorphic_associations.ipynb` showing the SPARQL that reads it —
reached here by **pointing at** the union rather than inlining a copy of it, so the
overlay cannot drift from core and no CDISC term is renamed. The deliverable stays at
660 triples.

**This is an authored edit to generated output, and it is named rather than
silent.** There is precedent inside the core: `20_generate.ipynb` replaces the
generated `owl:Ontology` node, because `ontology_uri_suffix` would otherwise name an
ontology after a file. The repair runs **after** the header is authored — before it,
the guard trips on the generated `owl:imports`, which is the literal relative import
path until the header replaces it — and it asserts the set of dangling IRIs is
exactly the expected one before repairing, and that nothing dangles after.

**Why this problem exists here and not in `usdm-rdf`, which is the part worth telling
CDISC.** A USDM coded attribute keeps `rdfs:range usdm:Code` and carries
`usdm:boundCodelist` to the codelist's NCIt C-code, letting NCIt name the permitted
values. `BiomedicalConceptResultScaleEnum` carries no `meaning:` on any of its five
values, so there is nothing to bind to and the generator's invented IRIs become **the
only identity a COSMoS result scale has anywhere**.

**But COSMoS is not uniformly unanchored, and the exception is what makes the ask
actionable.** `known-gaps.md` §4 already records it for the SDTM model:
`OriginTypeEnum` and `OriginSourceEnum` carry a `code_set` **and** a `meaning:` on
every permissible value, which is why decision D1 sees nine `NCIT_*` top-level classes
in that rendering. Adding the BC model, measured 2026-09-01: all three of its enums
are bare, so across both models **9 of 11 enums are bare and 2 are fully anchored**.

So the mechanism exists, CDISC already uses it, and it renders correctly through the
same generator on the same pin. The ask is therefore not "adopt terminology
governance" but **"do for the other nine enums what you already did for `OriginType`
and `OriginSource`"** — one `meaning:` line per permissible value, with an in-file
precedent to point at.

**Where the ask is harder than one line.** Anchoring needs a concept to point at, and
for result scale most of them do not exist. Verified 2026-09-01 against the NCI EVS
REST API, which is public: the only NCIt concept for the attribute, `Result Scale`
C227331, is NCI-authored with no CDISC contributing source, in no CDISC subset, and
with no members. At value level `Ordinal Scale` C47797 and `Nominal Scale` C47798
exist as proper scale concepts; there is no "Quantitative Scale", because quantitative
is a class of scales rather than one; and `Narrative` C80446 and `Temporal` C73990
exist only as generic concepts, not scales. Two of five anchor. Note also that
C227331's own definition names four scales and omits Temporal, which the COSMoS enum
includes.

That is the same gap as `known-gaps.md` §4 — the 33 predicate terms and 101 linking
phrases carrying no `code_set` and no per-value `meaning` — one layer down, on the
enums this repo actually renders.

---

## D21 — `data_type` on the BC↔DEC edge SETTLED 2026-09-02

**The defect, measured 2026-09-01.** `50_render_bc.ipynb` renders each data element
concept once, from whichever row arrives first. For `dec_label` and `ncit_dec_code`
that is correct — **0 of 226** distinct DECs carry more than one value. For
`data_type` and `example_set` it is not: they vary for **8** and **68** DECs
respectively, because they are properties of the **(BC, DEC) pair** and not of the
DEC. Six thousand and twenty-nine pairs collapse onto 226 nodes.

**What the shipped deliverable therefore says.** `cosmos_bc_v1.instances.ttl`
misstates `dataType` for **1,009 of 6,027** pairs, across **723 of 1,469** concepts
and 8 DECs, and `exampleSet` for **3,092** pairs across 68 DECs. `C70856` Observation
Result carries seven different `data_type` values across the pinned package — string
303, decimal 296, integer 53, datetime 12, boolean 6, float 2, duration 1. Glucose
`C105585` and HCV RNA `C142330` both publish it as **string**; the deliverable says
**decimal**.

**Settled: reify the BC→DEC edge as the concept's use of the DEC.** The shared node
`obo:NCIT_C70856` keeps what is constant — identity, `shortName`, `ncitCode`. A
node at `https://w3id.org/cdisc/cosmos/bc/{BC}/dec/{DEC}`, typed
`DataElementConcept`, carries `dataType` and `exampleSet` for that pair, plus
`shortName`, and reaches the shared node by `conceptId` rendered as an edge. The
concept's `dataElementConcepts` points at the use-node. It renders what the package
says, collapses nothing and invents nothing.

**Why the use-node is the honest reading of the schema, not a workaround.**
`dataElementConcepts` inlines a `DataElementConcept` whose `conceptId` is its
identifier. That inlined object *is* the pair: one per concept, with its own
`dataType`. The use-node renders the object the schema describes; the shared node
is what its identifier resolves to under decision D2. Both are typed
`DataElementConcept` because the schema has one class for both readings.

**Why under w3id and not under the concept's PURL.** The natural path
`obo:NCIT_C105585/dec/C70856` sits in OBO's namespace, which is not this repo's to
mint under. The use-node therefore lives under this repo's `bc/` segment, beside
the category nodes of D18 — one D7 revisit for both.

**Measured after the change.** 6,004 use-nodes (6,029 pairs at the latest package
date; 6,027 with an identified DEC; 6,004 with both sides identified), 224 shared
nodes, 63,030 triples against 29,697 before, 4.1 MB against 1.6 MB, no blank nodes,
byte-identical on macOS and Linux. The renderer asserts that no pair carries more
than one `data_type` or `example_set` — true at this pin — so if the grain ever
moves again, generation fails rather than collapsing silently.

**What it costs in the conformance report, and why the cost is the finding.**
Three causes of 6,004 each — the use-node's `conceptId` is an IRI where the
published shape says `xsd:string`, `sh:Literal`, and pattern `^(C[0-9]+|NEW_…)$`
— and one of 224: `sh:minCount 1` on `dataType`, which the shared node no longer
carries. That last one is the D21 finding stated by CDISC's own shape: it
requires exactly one data type on a data element concept, and at this pin a data
element concept has up to seven.

**Consequence for the merged graph.** Before this decision a consumer loading core
and overlay together saw Observation Result as `decimal` in core and `float` in
the overlay for glucose — the wrong disagreement. Now the core pair says `string`
and the overlay pair says `float`, which is the inherit-once argument the overlay
exists to make, readable from the graph rather than from prose.

**Rejected: multi-value them on the DEC node.** Nothing is dropped, but which BC said
which is lost — `C70856` would simply be seven types — and it violates the published
`sh:maxCount 1` while saying less than the reified form.

**Rejected: drop them and report in CSV.** Strictly derived and free of
contradiction, but it removes from the graph the very attribute the overlay's
inherit-once argument is about.

**Already exercised in the overlay.** `75_render_qbc.ipynb` renders a data element
concept as the qualified concept's **use** of it — a node at `{concept}/dec/{code}`
carrying `dataType` and `exampleSet`, linked to the shared NCIt concept by
`cosmos_bc:conceptId` rendered as an edge — and asserts that no `dataType` is ever
written onto a shared NCIt node. So the shape core is moving to is already in the
repo and already validated.

**Why this matters beyond the fix.** It is the strongest independent evidence for the
claim the overlay exists to make. The sibling schema annotates its result DEC
`dataType: float  # AUTHORITATIVE (today: string)`. That is not merely an opinion
about where the type should live: measured at this pin, `dataType` is **not a
property of the data element concept at all** in what CDISC publishes. It is a
property of the edge, which is why one DEC can be seven types at once, and why
"inherit once from the result DEC" is impossible today rather than merely unusual.

**Shipped with D18** on 2026-09-02 — one re-render, one set of baselines.

---

## Carried over from `usdm-rdf` without re-argument

These are settled there and adopted here by reference, not re-decided:

- Slash semantics for the ontology IRI, not hash.
- Whole-graph dereference by content negotiation, per-IRI HTML anchors.
- A generic `versionIRI` rewrite rule so releases need no new w3id PR.
- Fail-fast generation; no defensive handling of source data that should not
  need it.

See `usdm-rdf/docs/iri-and-governance.md` for the arguments.
