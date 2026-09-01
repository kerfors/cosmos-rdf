# Decisions

Numbered decisions for this repo, in the style of `usdm-rdf`
`docs/iri-and-governance.md` (D1–D6 there). Each is an argument, not a code
change; a decision moves from OPEN to SETTLED only when it has been acted on.

Five decisions are open at P0. They are the ones named in the kickoff brief.
Nothing below has been implemented.

---

## D1 — One core graph or two OPEN

**Question.** Publish one merged core rendering of COSMoS, or two —
`cosmos_bc_v1.ttl` and `cosmos_sdtm_v1.ttl`?

**Forcing fact.** The six slot names declared in both published schemas
(`known-gaps.md` §1). OWL and SHACL generation tolerate the collision; a JSON-LD
context and any instance conversion do not.

**The two options.**

- *Two graphs.* Honest to the source — CDISC publishes two schemas with two
  namespace ids (`…/biomedical_concept_v1.0`, `…/sdtm_v1.0`). Cheap: the probe
  showed `gen-owl` succeeds per schema with no new code. Costs the consumer a
  second import and leaves the collision visible rather than resolved.
- *One merged graph.* Friendlier to consumers, and closer to how the content is
  actually used (the BC→DSS hop is the interesting edge). Requires an explicit
  `slot_uri` for each of the six colliding names, which is **this repo deciding
  something the standard did not** — exactly the kind of authored content the
  core layer is supposed to exclude (§9 of the kickoff brief).

**Bearing.** The layering rule says core is mechanical and opinion goes in the
overlay. Disambiguating six names is opinion, however small.

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

## Carried over from `usdm-rdf` without re-argument

These are settled there and adopted here by reference, not re-decided:

- Slash semantics for the ontology IRI, not hash.
- Whole-graph dereference by content negotiation, per-IRI HTML anchors.
- A generic `versionIRI` rewrite rule so releases need no new w3id PR.
- Fail-fast generation; no defensive handling of source data that should not
  need it.

See `usdm-rdf/docs/iri-and-governance.md` for the arguments.
