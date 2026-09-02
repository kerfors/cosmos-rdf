"""CI guard: deliverable integrity checks for the committed artifacts.

Verifies that the nine generated deliverables at repo root parse and match the
operational baselines, and that the structural guarantees the decisions rest on
still hold: no malformed IRI in a CDISC namespace (docs/known-gaps.md 1a); in the
core T-Boxes nothing but the ontology and its version in the w3id namespace
(decision D7); and in every other deliverable, every w3id IRI matches one of the
forms a decision admits by name (D3, D13, D17, D18, D21) - so a new minting has to
be argued here before it can pass.

This is a guard against broken or partial commits, not a re-run of the pipeline.
The deep checks live in notebooks/30_validate.ipynb, 60_validate_instances.ipynb
and 65_compare_render_paths.ipynb.

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
VERSION = "0.1.0"

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

# The overlay (D13-D21). Its T-Box mints terms under w3id by decision, so the D7
# check above does not apply to it; the check is instead that every w3id IRI it
# carries is its own, or the core BC ontology it imports.
OVERLAY_TBOX = "cosmos_qbc_v1.ttl"
OVERLAY_TBOX_TRIPLES = 660
OVERLAY_CLASSES = 9            # declared classes; enum permissible values excluded
OVERLAY_INSTANCES = "cosmos_qbc_v1.instances.ttl"
OVERLAY_INSTANCE_TRIPLES = 467
OVERLAY_CONCEPTS = 6
OVERLAY_RECORDINGS = 8

# Every form a w3id IRI may take in the two A-Boxes, each admitted by a decision.
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
        (r"qbc/[A-Za-z]+/(dec|mapping|value|regime)/[^/]+(/[^/]+)?$", "a qualified concept's own nodes (D15, D16, D21)"),
        (r"dss/[A-Z]+/[A-Z][A-Z0-9_]*$", "a recording IS the Dataset Specialization IRI (D3, D17)"),
        (r"dss/[A-Z]+/[A-Z][A-Z0-9_]*/specimen$", "a recording's specimen (D17)"),
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

# 7. The overlay T-Box (D13): parses, declares its nine classes, imports the core
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

# 8. The overlay A-Box (D13-D21): parses, counts match, joins the core A-Box by
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
check(f"{OVERLAY_INSTANCES} w3id IRIs outside the admitted forms", unadmitted(overlay_instances, W3ID_ADMITTED[OVERLAY_INSTANCES]), [])

if failures:
    print(f"\n{len(failures)} check(s) failed: {', '.join(failures)}")
    sys.exit(1)
print("\nAll deliverable integrity checks passed.")
