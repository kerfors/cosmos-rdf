"""CI guard: deliverable integrity checks for the committed artifacts.

Verifies that the ten generated deliverables at repo root and the 32 Dataset
Specialization graphs under dss/ parse and match the operational baselines, and
that the structural guarantees the decisions rest on still hold: no malformed
IRI in a CDISC namespace (docs/known-gaps.md 1a); in the core T-Boxes nothing
but the ontology and its version in the w3id namespace (decision D7); and in
every other deliverable, every w3id IRI matches one of the
forms a decision admits by name (D3, D13, D17, D18, D21, D23, D26, D28, D30) - so a
new minting has to be argued here before it can pass; in the overlay shapes, every
enum constraint holds IRIs and the result-scale lists hold exactly the admitted set
(D24); and in every domain graph the variable order is carried as rdf:_n beside the
variables edges (D27), nothing is written onto an NCIt node but a codelist (D28,
D29), and only the SDTM T-Box is imported (D32).

This is a guard against broken or partial commits, not a re-run of the pipeline.
The deep checks live in notebooks/30_validate.ipynb, 60_validate_instances.ipynb,
62_validate_dss_instances.ipynb and 65_compare_render_paths.ipynb.

Baselines below are a further copy of the numbers in those notebooks and in
README.md. When the pinned commit is bumped and baselines drift, update all of
them (see CLAUDE.md, "Source pinning").

Lineage: adapted from usdm-rdf/scripts/ci_check.py. See scripts/LINEAGE.md.

Requires rdflib only. Run from repo root: python scripts/ci_check.py
"""

import json
import re
import sys

from rdflib import BNode, Graph, URIRef
from rdflib.namespace import OWL, RDF, SH

BC_NS = "https://www.cdisc.org/cosmos/biomedical_concept_v1.0"
SDTM_NS = "https://www.cdisc.org/cosmos/sdtm_v1.0"
W3ID = "https://w3id.org/cdisc/cosmos/"
QBC_NS = W3ID + "qbc/"
VERSION = "0.4.0"

# Operational baselines: COSMoS commit 031429b1, package date 2026-07-14.
ONTOLOGIES = {
    "cosmos_bc_v1.ttl": {
        "triples": 535,
        "classes": 21,
        "namespace": BC_NS,
        "ontology_iri": W3ID + "bc/",
    },
    "cosmos_sdtm_v1.ttl": {
        "triples": 2028,
        "classes": 170,
        "namespace": SDTM_NS,
        "ontology_iri": W3ID + "sdtm/",
    },
}

SHAPES = {
    "cosmos_bc_v1.shapes.ttl": {"triples": 204, "node_shapes": 3},
    "cosmos_sdtm_v1.shapes.ttl": {"triples": 679, "node_shapes": 7},
}

CONTEXTS = {
    "cosmos_bc_v1.context.jsonld": 27,
    "cosmos_sdtm_v1.context.jsonld": 56,
}

INSTANCES = "cosmos_bc_v1.instances.ttl"
INSTANCE_TRIPLES = 63030
INSTANCE_CONCEPTS = 1469
INSTANCE_DECS_SHARED = 224     # D21: the shared NCIt node per data element concept
INSTANCE_DEC_USES = 6004       # D21: one node per (concept, DEC) pair
INSTANCE_CATEGORIES = 405      # D18: label-nodes

# The overlay (D13-D23). Its T-Box mints terms under w3id by decision, so the D7
# check above does not apply to it; the check is instead that every w3id IRI it
# carries is its own, or the core BC ontology it imports.
OVERLAY_TBOX = "cosmos_qbc_v1.ttl"
OVERLAY_TBOX_TRIPLES = 725
OVERLAY_CLASSES = 10           # declared classes; enum permissible values excluded
OVERLAY_INSTANCES = "cosmos_qbc_v1.instances.ttl"
OVERLAY_INSTANCE_TRIPLES = 515
OVERLAY_CONCEPTS = 6
OVERLAY_RECORDINGS = 8
OVERLAY_SCALES = 3             # D23: the result scales the overlay admits, anchored to NCIt
OVERLAY_SHAPES = "cosmos_qbc_v1.shapes.ttl"
OVERLAY_SHAPES_TRIPLES = 366
OVERLAY_NODE_SHAPES = 9

# The Dataset Specialization A-Box (D26-D32): one graph per domain under dss/.
DSS_DIR = "dss"
DSS_TRIPLES = {
    "AE": 1652, "BE": 694, "CM": 1788, "DD": 1559, "DM": 231, "DS": 2264, "EC": 670,
    "EG": 7789, "EX": 354, "FA": 2158, "FT": 5819, "GF": 12121, "IE": 305, "IS": 86542,
    "LB": 35093, "MB": 2990, "MH": 2713, "MI": 1839, "MK": 10443, "PR": 3436, "QS": 3394,
    "RE": 23031, "RP": 13285, "RS": 27141, "SC": 10106, "SR": 2535, "SU": 4059, "TR": 2760,
    "TS": 12350, "TU": 2644, "UR": 1951, "VS": 14065,
}
DSS_GROUPS = 1475
DSS_VARIABLES = 13922
DSS_ASSIGNED_TERMS = 4776      # D28: one node per use
DSS_RELATIONSHIPS = 13585      # D30
DSS_CODELISTS = 297            # D29: distinct shared nodes across all domain files
DSS_BC_LITERALS = 4            # D31: references to NEW_ concepts, carried as the published string
DSS_DEC_LITERALS = 1           # D31: NEW_DEC1

# Every form a w3id IRI may take in the A-Boxes, each admitted by a decision.
# Anything else in the w3id namespace fails: a new minting must be added here
# with its decision number, never by accident.
W3ID_ADMITTED = {
    INSTANCES: [
        (r"bc/$", "core BC ontology, imported (D7)"),
        (r"bc/instances/$", "this graph's ontology IRI"),
        (r"bc/instances/" + re.escape(VERSION) + r"$", "this graph's version IRI"),
        (r"bc/category/[^/]+$", "category label-node (D18)"),
        (r"bc/C[0-9]+/dec/C[0-9]+$", "a concept's use of a data element concept (D21)"),
    ],
    OVERLAY_INSTANCES: [
        (r"bc/instances/$", "core BC A-Box, imported"),
        (r"qbc/$", "overlay ontology, imported (D13)"),
        (r"qbc/instances/$", "this graph's ontology IRI"),
        (r"qbc/instances/" + re.escape(VERSION) + r"$", "this graph's version IRI"),
        (r"qbc/[A-Za-z]+$", "an overlay term, or a qualified concept (D13)"),
        (r"qbc/[A-Za-z]+Enum#[A-Za-z]+$", "an overlay permissible value (D20)"),
        (r"qbc/[A-Za-z]+/(dec|mapping|value|regime|specimen)/[^/]+(/[^/]+)?$", "a qualified concept's own nodes (D15, D16, D21, D22)"),
        (r"qbc/scale/[A-Za-z]+$", "a result scale the overlay admits (D23)"),
        (r"qbc/scale/[A-Za-z]+/mapping/C[0-9]+$", "an admitted result scale's NCIt anchor (D23)"),
        (r"dss/[A-Z]+/[A-Z][A-Z0-9_]*$", "a recording IS the Dataset Specialization IRI (D3, D17)"),
        (r"dss/[A-Z]+/[A-Z][A-Z0-9_]*/specimen$", "a recording's specimen (D17)"),
    ],
    DSS_DIR: [
        (r"sdtm/$", "core SDTM ontology, imported (D7, D32)"),
        (r"dss/[A-Z]+$", "this graph's ontology IRI (D32)"),
        (r"dss/[A-Z]+/" + re.escape(VERSION) + r"$", "this graph's version IRI (D32)"),
        (r"dss/[A-Z]+/[A-Z][A-Z0-9_]*$", "a Dataset Specialization (D3)"),
        (r"dss/[A-Z]+/[A-Z][A-Z0-9_]*/[A-Z][A-Z0-9_]*$", "a variable of a specialization (D26)"),
        (r"dss/[A-Z]+/[A-Z][A-Z0-9_]*/[A-Z][A-Z0-9_]*/assignedTerm$", "a variable's assigned term (D28)"),
        (r"dss/[A-Z]+/[A-Z][A-Z0-9_]*/[A-Z][A-Z0-9_]*/relationship$", "a variable's relationship (D30)"),
    ],
}

JSONLD_VERSION = 1.1

failures = []


def check(name, actual, expected):
    if actual == expected:
        print(f"ok    {name}: {actual}")
    else:
        print(f"FAIL  {name}: expected {expected}, got {actual}")
        failures.append(name)


def iris(graph):
    found = set()
    for triple in graph:
        for node in triple:
            if isinstance(node, URIRef):
                found.add(str(node))
    return found


# 1. Ontologies parse; triples, classes, ontology IRI and version IRI match.
graphs = {}
for target, expected in ONTOLOGIES.items():
    graph = Graph().parse(target, format="turtle")
    graphs[target] = graph

    check(f"{target} triples", len(graph), expected["triples"])
    check(
        f"{target} owl:Class",
        sum(1 for c in graph.subjects(RDF.type, OWL.Class) if isinstance(c, URIRef)),
        expected["classes"],
    )
    check(
        f"{target} ontology IRI",
        [str(s) for s in graph.subjects(RDF.type, OWL.Ontology)],
        [expected["ontology_iri"]],
    )
    check(
        f"{target} owl:versionIRI",
        [str(o) for o in graph.objects(URIRef(expected["ontology_iri"]), OWL.versionIRI)],
        [expected["ontology_iri"] + VERSION],
    )

    # known-gaps.md 1a: every IRI in a CDISC namespace carries a separator.
    exempt = {expected["namespace"], expected["namespace"] + ".owl.ttl"}
    malformed = sorted(
        iri
        for iri in iris(graph)
        if iri.startswith(expected["namespace"])
        and iri not in exempt
        and not iri.startswith(expected["namespace"] + "/")
    )
    check(f"{target} malformed IRIs", malformed, [])

    # Decision D7: the w3id namespace holds the ontology and its version, nothing else.
    check(
        f"{target} IRIs in the w3id namespace",
        sorted(iri for iri in iris(graph) if iri.startswith(W3ID)),
        sorted({expected["ontology_iri"], expected["ontology_iri"] + VERSION}),
    )

# 2. Decision D1: the two ontologies share no IRI of the other's namespace.
check(
    "cosmos_bc_v1.ttl free of SDTM-namespace IRIs",
    sorted(i for i in iris(graphs["cosmos_bc_v1.ttl"]) if i.startswith(SDTM_NS)),
    [],
)
check(
    "cosmos_sdtm_v1.ttl free of BC-namespace IRIs",
    sorted(i for i in iris(graphs["cosmos_sdtm_v1.ttl"]) if i.startswith(BC_NS)),
    [],
)

# 3. Shapes parse; triples and NodeShape counts match.
for target, expected in SHAPES.items():
    graph = Graph().parse(target, format="turtle")
    check(f"{target} triples", len(graph), expected["triples"])
    check(
        f"{target} sh:NodeShape",
        sum(1 for _ in graph.subjects(RDF.type, SH.NodeShape)),
        expected["node_shapes"],
    )

# 4. Contexts are valid JSON with a single top-level @context, declare JSON-LD
#    1.1, and map conceptId to @id (the hinge of decision D2).
for target, expected_terms in CONTEXTS.items():
    with open(target, encoding="utf-8") as f:
        document = json.load(f)
    check(f"{target} top-level keys", sorted(document), ["@context"])
    context = document["@context"]
    check(f"{target} @version", context.get("@version"), JSONLD_VERSION)
    check(f"{target} conceptId mapping", context.get("conceptId"), "@id")
    check(f"{target} terms", len(context) - 1, expected_terms)

# 5. The A-Box parses; counts match and no blank node survives (decision D10).
instances = Graph().parse(INSTANCES, format="turtle")
bc_class = URIRef(BC_NS + "/BiomedicalConcept")
dec_class = URIRef(BC_NS + "/DataElementConcept")
data_type = URIRef(BC_NS + "/dataType")
categories = URIRef(BC_NS + "/categories")
label = URIRef("http://www.w3.org/2000/01/rdf-schema#label")

dec_nodes = set(instances.subjects(RDF.type, dec_class))
dec_uses = {s for s in dec_nodes if "/dec/" in str(s)}
dec_shared = dec_nodes - dec_uses
category_nodes = set(instances.objects(None, categories))

check(f"{INSTANCES} triples", len(instances), INSTANCE_TRIPLES)
check(
    f"{INSTANCES} BiomedicalConcept nodes",
    len(set(instances.subjects(RDF.type, bc_class))),
    INSTANCE_CONCEPTS,
)
check(f"{INSTANCES} shared DataElementConcept nodes", len(dec_shared), INSTANCE_DECS_SHARED)
check(f"{INSTANCES} (concept, DEC) use-nodes", len(dec_uses), INSTANCE_DEC_USES)
check(f"{INSTANCES} category nodes", len(category_nodes), INSTANCE_CATEGORIES)
check(
    f"{INSTANCES} blank nodes",
    len({s for s in instances.subjects() if isinstance(s, BNode)}),
    0,
)

# Decision D21: dataType lives on the pair, never on the shared node.
check(
    f"{INSTANCES} dataType on a shared DEC node",
    sorted(str(s) for s in dec_shared if (s, data_type, None) in instances),
    [],
)
# Decision D18: a category node carries a label and nothing else.
check(
    f"{INSTANCES} category nodes without a label",
    sorted(str(c) for c in category_nodes if (c, label, None) not in instances),
    [],
)
check(
    f"{INSTANCES} category nodes asserting more than a label",
    sorted(str(c) for c in category_nodes if any(p != label for p in instances.predicates(c))),
    [],
)


# 6. Every w3id IRI in an A-Box takes a form a decision admits by name.
def unadmitted(graph, admitted):
    rules = [re.compile(W3ID + pattern) for pattern, _ in admitted]
    return sorted(
        iri for iri in iris(graph)
        if iri.startswith(W3ID) and not any(rule.match(iri) for rule in rules)
    )


check(f"{INSTANCES} w3id IRIs outside the admitted forms", unadmitted(instances, W3ID_ADMITTED[INSTANCES]), [])

# 7. The overlay T-Box (D13): parses, declares its ten classes, imports the core
#    BC ontology, and every w3id IRI in it is either its own or that import.
overlay = Graph().parse(OVERLAY_TBOX, format="turtle")
overlay_classes = {
    str(s) for s in overlay.subjects(RDF.type, OWL.Class)
    if isinstance(s, URIRef) and str(s).startswith(QBC_NS) and "#" not in str(s)
}
check(f"{OVERLAY_TBOX} triples", len(overlay), OVERLAY_TBOX_TRIPLES)
check(f"{OVERLAY_TBOX} declared classes", len(overlay_classes), OVERLAY_CLASSES)
check(f"{OVERLAY_TBOX} ontology IRI", [str(s) for s in overlay.subjects(RDF.type, OWL.Ontology)], [QBC_NS])
check(f"{OVERLAY_TBOX} owl:versionIRI", [str(o) for o in overlay.objects(URIRef(QBC_NS), OWL.versionIRI)], [QBC_NS + VERSION])
check(f"{OVERLAY_TBOX} owl:imports", [str(o) for o in overlay.objects(URIRef(QBC_NS), OWL.imports)], [W3ID + "bc/"])
check(
    f"{OVERLAY_TBOX} w3id IRIs outside qbc/ and the core import",
    sorted(
        iri for iri in iris(overlay)
        if iri.startswith(W3ID) and not iri.startswith(QBC_NS)
        and iri not in {W3ID + "bc/", W3ID + "qbc"}   # the bare schema id is gen-owl's skos:inScheme
    ),
    [],
)
check(
    f"{OVERLAY_TBOX} CDISC terms redeclared under qbc/",
    sorted(iri for iri in iris(overlay) if iri.startswith(QBC_NS) and iri.rsplit("/", 1)[-1].split("#")[0] in {
        "BiomedicalConcept", "DataElementConcept", "Coding",
        "BiomedicalConceptResultScaleEnum", "DataElementConceptDataTypeEnum", "PackageTypeEnum",
    }),
    [],
)

# 8. The overlay A-Box (D13-D23): parses, counts match, joins the core A-Box by
#    skos:broader, and every w3id IRI takes an admitted form.
overlay_instances = Graph().parse(OVERLAY_INSTANCES, format="turtle")
qbc_concept = URIRef(QBC_NS + "QualifiedBiomedicalConcept")
qbc_recording = URIRef(QBC_NS + "Recording")
broader = URIRef("http://www.w3.org/2004/02/skos/core#broader")

check(f"{OVERLAY_INSTANCES} triples", len(overlay_instances), OVERLAY_INSTANCE_TRIPLES)
check(f"{OVERLAY_INSTANCES} qualified concepts", len(set(overlay_instances.subjects(RDF.type, qbc_concept))), OVERLAY_CONCEPTS)
check(f"{OVERLAY_INSTANCES} recordings", len(set(overlay_instances.subjects(RDF.type, qbc_recording))), OVERLAY_RECORDINGS)
check(
    f"{OVERLAY_INSTANCES} skos:broader targets not typed BiomedicalConcept in {INSTANCES}",
    sorted(str(o) for o in overlay_instances.objects(None, broader) if (o, RDF.type, bc_class) not in instances),
    [],
)
check(
    f"{OVERLAY_INSTANCES} dataType on a node the core A-Box describes",
    sorted(str(s) for s, _, _ in overlay_instances.triples((None, data_type, None)) if (s, None, None) in instances),
    [],
)
# Decision D22: the overlay writes onto its own nodes only. Shared NCIt concepts
# are reached by edges and are never the subject of an overlay triple.
check(
    f"{OVERLAY_INSTANCES} NCIt PURLs used as a subject",
    sorted(str(s) for s in set(overlay_instances.subjects()) if str(s).startswith("http://purl.obolibrary.org/obo/NCIT_")),
    [],
)
check(f"{OVERLAY_INSTANCES} w3id IRIs outside the admitted forms", unadmitted(overlay_instances, W3ID_ADMITTED[OVERLAY_INSTANCES]), [])

# Decision D23: the overlay admits exactly three result scales - Nominal, Ordinal,
# Quantitative - as nodes of its own, each the use of a core permissible value;
# Temporal and Narrative get no node (known-gaps.md 4a); and every qualified
# concept's resultScale is one of the admitted values.
qbc_scale = URIRef(QBC_NS + "ResultScale")
permissible_value = URIRef(QBC_NS + "permissibleValue")
result_scale = URIRef(QBC_NS + "resultScale")
scale_enum = BC_NS + "/BiomedicalConceptResultScaleEnum#"
scale_nodes = set(overlay_instances.subjects(RDF.type, qbc_scale))
admitted_scales = {o for s in scale_nodes for o in overlay_instances.objects(s, permissible_value)}
core_scales = {
    s for s in graphs["cosmos_bc_v1.ttl"].subjects(RDF.type, OWL.Class)
    if isinstance(s, URIRef) and str(s).startswith(scale_enum)
}
check(f"{OVERLAY_INSTANCES} admitted result scales", len(scale_nodes), OVERLAY_SCALES)
check(
    f"{OVERLAY_INSTANCES} admitted result scale values",
    sorted(str(v).replace(scale_enum, "") for v in admitted_scales),
    ["Nominal", "Ordinal", "Quantitative"],
)
check(
    f"{OVERLAY_INSTANCES} core permissible values left without a node",
    sorted(str(v).replace(scale_enum, "") for v in core_scales - admitted_scales),
    ["Narrative", "Temporal"],
)
check(
    f"{OVERLAY_INSTANCES} resultScale values outside the admitted set",
    sorted(str(v) for v in set(overlay_instances.objects(None, result_scale)) - admitted_scales),
    [],
)

# 9. The overlay shapes (D24): parse, counts match, no shape targets an imported
#    BC class, every sh:in member is an IRI, and the two result-scale lists hold
#    exactly the admitted set of D23.
from rdflib.collection import Collection

overlay_shapes = Graph().parse(OVERLAY_SHAPES, format="turtle")
check(f"{OVERLAY_SHAPES} triples", len(overlay_shapes), OVERLAY_SHAPES_TRIPLES)
check(f"{OVERLAY_SHAPES} sh:NodeShape", sum(1 for _ in overlay_shapes.subjects(RDF.type, SH.NodeShape)), OVERLAY_NODE_SHAPES)
check(
    f"{OVERLAY_SHAPES} shapes targeting an imported BC class",
    sorted(str(o) for o in overlay_shapes.objects(None, SH.targetClass) if str(o).startswith(BC_NS)),
    [],
)
in_lists = {
    str(overlay_shapes.value(shape, SH.path)).replace(QBC_NS, ""): list(Collection(overlay_shapes, lst))
    for shape, lst in overlay_shapes.subject_objects(SH["in"])
}
check(f"{OVERLAY_SHAPES} properties constrained by sh:in", sorted(in_lists), ["permissibleValue", "relation", "resultScale"])
check(
    f"{OVERLAY_SHAPES} sh:in members that are not IRIs",
    sorted(str(v) for members in in_lists.values() for v in members if not isinstance(v, URIRef)),
    [],
)
for prop in ("resultScale", "permissibleValue"):
    check(
        f"{OVERLAY_SHAPES} {prop} sh:in equals the admitted result scales",
        sorted(str(v) for v in in_lists.get(prop, [])),
        sorted(str(v) for v in admitted_scales),
    )

# 10. The Dataset Specialization A-Box (D26-D32): every domain file parses to its
#     baseline, names itself and its version, imports the SDTM T-Box and nothing
#     else, carries the D27 order as rdf:_n mirroring the variables edges, writes
#     onto no NCIt node but a codelist, and mints only admitted forms. Counts are
#     summed across files, except codelist nodes, which repeat per file (D32) and
#     are counted distinct.
from pathlib import Path

sdtm_group = URIRef(SDTM_NS + "/SDTMGroup")
sdtm_variable = URIRef(SDTM_NS + "/SDTMVariable")
assigned_term = URIRef(SDTM_NS + "/AssignedTerm")
relationship = URIRef(SDTM_NS + "/RelationShip")
codelist = URIRef(SDTM_NS + "/CodeList")
variables = URIRef(SDTM_NS + "/variables")
bc_id = URIRef(SDTM_NS + "/biomedicalConceptId")
dec_id = URIRef(SDTM_NS + "/dataElementConceptId")
rdf_member = str(RDF) + "_"

dss_files = sorted(Path(DSS_DIR).glob("cosmos_sdtm_v1.*.instances.ttl"))
check(f"{DSS_DIR}/ domain files", [f.name.split(".")[1] for f in dss_files], sorted(DSS_TRIPLES))

dss_totals = {"groups": 0, "variables": 0, "members": 0, "terms": 0, "relationships": 0,
              "bc_literals": 0, "dec_literals": 0, "blank": 0}
dss_codelists = set()
dss_unadmitted = []
for file in dss_files:
    domain = file.name.split(".")[1]
    graph = Graph().parse(file, format="turtle")
    ontology_iri = f"{W3ID}dss/{domain}"
    check(f"{file.name} triples", len(graph), DSS_TRIPLES[domain])
    check(f"{file.name} ontology IRI", [str(s) for s in graph.subjects(RDF.type, OWL.Ontology)], [ontology_iri])
    check(f"{file.name} owl:versionIRI", [str(o) for o in graph.objects(URIRef(ontology_iri), OWL.versionIRI)], [f"{ontology_iri}/{VERSION}"])
    check(f"{file.name} owl:imports", [str(o) for o in graph.objects(URIRef(ontology_iri), OWL.imports)], [W3ID + "sdtm/"])
    member_edges = {(s, o) for s, p, o in graph if str(p).startswith(rdf_member)}
    variable_edges = set(graph.subject_objects(variables))
    check(f"{file.name} rdf:_n edges mirror the variables edges (D27)", member_edges == variable_edges, True)
    check(
        f"{file.name} NCIt nodes used as a subject that are not codelists (D28, D29)",
        sorted(str(s) for s in set(graph.subjects()) if str(s).startswith("http://purl.obolibrary.org/obo/NCIT_")
               and (s, RDF.type, codelist) not in graph),
        [],
    )
    dss_unadmitted += unadmitted(graph, W3ID_ADMITTED[DSS_DIR])
    dss_totals["groups"] += len(set(graph.subjects(RDF.type, sdtm_group)))
    dss_totals["variables"] += len(set(graph.subjects(RDF.type, sdtm_variable)))
    dss_totals["members"] += len(member_edges)
    dss_totals["terms"] += len(set(graph.subjects(RDF.type, assigned_term)))
    dss_totals["relationships"] += len(set(graph.subjects(RDF.type, relationship)))
    dss_totals["bc_literals"] += sum(1 for o in graph.objects(None, bc_id) if not isinstance(o, URIRef))
    dss_totals["dec_literals"] += sum(1 for o in graph.objects(None, dec_id) if not isinstance(o, URIRef))
    dss_totals["blank"] += len({s for s in graph.subjects() if isinstance(s, BNode)})
    dss_codelists |= set(graph.subjects(RDF.type, codelist))

check(f"{DSS_DIR}/ SDTMGroup nodes", dss_totals["groups"], DSS_GROUPS)
check(f"{DSS_DIR}/ SDTMVariable nodes", dss_totals["variables"], DSS_VARIABLES)
check(f"{DSS_DIR}/ rdf:_n edges (D27)", dss_totals["members"], DSS_VARIABLES)
check(f"{DSS_DIR}/ AssignedTerm nodes (D28)", dss_totals["terms"], DSS_ASSIGNED_TERMS)
check(f"{DSS_DIR}/ RelationShip nodes (D30)", dss_totals["relationships"], DSS_RELATIONSHIPS)
check(f"{DSS_DIR}/ distinct CodeList nodes (D29)", len(dss_codelists), DSS_CODELISTS)
check(f"{DSS_DIR}/ biomedicalConceptId literals (D31)", dss_totals["bc_literals"], DSS_BC_LITERALS)
check(f"{DSS_DIR}/ dataElementConceptId literals (D31)", dss_totals["dec_literals"], DSS_DEC_LITERALS)
check(f"{DSS_DIR}/ blank nodes", dss_totals["blank"], 0)
check(f"{DSS_DIR}/ w3id IRIs outside the admitted forms", sorted(set(dss_unadmitted)), [])

if failures:
    print(f"\n{len(failures)} check(s) failed: {', '.join(failures)}")
    sys.exit(1)
print("\nAll deliverable integrity checks passed.")
