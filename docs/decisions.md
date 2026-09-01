# Decisions

Numbered decisions for this repo, in the style of `usdm-rdf`
`docs/iri-and-governance.md` (D1–D6 there). Each is an argument, not a code
change; a decision moves from OPEN to SETTLED only when it has been acted on.

D1, D6 and D7 are settled and implemented. D2–D5 are open; they are the ones
named in the kickoff brief.

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

## D2 — Identity binding for concept codes OPEN

**Question.** How does a bare C-code in the export become a subject IRI?

**Proposal.** Adopt `usdm-rdf` decision D4 unchanged — the **dual anchor**: the
NCI EVS Thesaurus identifier (the form CDISC Library RDF uses) plus the
resolvable OBO PURL, always both. Consistency across the two repos is worth more
than any refinement here, and the argument for it is already written.

**Why it is load-bearing.** The 2026-08-30 probe stopped at
`DataElementConcept.conceptId`: an `identifier` slot holding a bare C-code with
no prefix binding to mint an IRI from. LinkML rejects `@base` as a prefix name,
so the fix is a proper NCIT prefix binding / `id_prefixes`, not a base hack.
Until this is settled, instance conversion does not run at all.

**Note.** The BC `conceptId` pattern is `^(C[0-9]+|NEW_[A-Z_]*[0-9]*)$` — it
admits `NEW_*` placeholders that are **not** NCIt codes and cannot be anchored.
Their handling is part of this decision, not a detail of it.

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

## Carried over from `usdm-rdf` without re-argument

These are settled there and adopted here by reference, not re-decided:

- Slash semantics for the ontology IRI, not hash.
- Whole-graph dereference by content negotiation, per-IRI HTML anchors.
- A generic `versionIRI` rewrite rule so releases need no new w3id PR.
- Fail-fast generation; no defensive handling of source data that should not
  need it.

See `usdm-rdf/docs/iri-and-governance.md` for the arguments.
