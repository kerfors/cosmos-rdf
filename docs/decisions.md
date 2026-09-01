# Decisions

Numbered decisions for this repo, in the style of `usdm-rdf`
`docs/iri-and-governance.md` (D1–D6 there). Each is an argument, not a code
change; a decision moves from OPEN to SETTLED only when it has been acted on.

D1, D2 and D6–D9 are settled and implemented. D3, D4 and D5 remain open.

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

## D3 — DSS identity OPEN — the load-bearing one

**Question.** What is the subject IRI of a Dataset Specialization?

**Facts** (`known-gaps.md` §6): `datasetSpecializationId` is declared
`identifier: true`; its pattern enforces only an uppercase mnemonic; nothing
enforces cross-domain uniqueness; measured today, 0 of 1,475 collide.

**Proposal.** Mint **domain-scoped** IRIs. Carry the mnemonic as
`dcterms:identifier`. Do not depend on the mnemonic alone even though it would
work at this package.

**Why not just use the mnemonic.** Because a rendering that silently relies on an
unguaranteed property teaches consumers that the property is guaranteed. The gap
is the finding; hiding it behind a working IRI scheme would delete the finding.
State it in `known-gaps.md` and mint around it.

---

## D4 — A-Box scope OPEN

**Question.** Render the full package (1,475 DSS, 1,475 BC), or T-Box plus a
small set of worked instances first?

**Bearing.** The kickoff brief is explicit that P0–P2 is publishable on its own
and that P3 should not be committed to until P2 shows the identity binding
holds. An OWL + SHACL rendering of COSMoS does not exist anywhere today; a
partial A-Box on top of it is a smaller claim than a full one, and a full A-Box
built on an unsettled D2/D3 would have to be reissued.

---

## D5 — Row-order dependency OPEN

**Question.** May `variables` ordering rely on CSV row order?

**Facts.** The DSS model requires an *ordered* `variables` list. The export has
no order column; order survives only as file row order, and row blocks are
contiguous (0 interleaved at this pin).

**The two options.** Rely on row order and **state the dependency explicitly**
in the deliverable's provenance — or reconstruct order from SDTM convention
(TESTCD, TEST, CAT, ORRES, …) and state *that* as a rule this repo applies.

**Bearing.** The first is derived-not-asserted but depends on a file convention
CDISC has not documented as a contract. The second is an assertion this repo
makes, which belongs in the overlay, not the core.

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

## Carried over from `usdm-rdf` without re-argument

These are settled there and adopted here by reference, not re-decided:

- Slash semantics for the ontology IRI, not hash.
- Whole-graph dereference by content negotiation, per-IRI HTML anchors.
- A generic `versionIRI` rewrite rule so releases need no new w3id PR.
- Fail-fast generation; no defensive handling of source data that should not
  need it.

See `usdm-rdf/docs/iri-and-governance.md` for the arguments.
