"""CI guard: deliverable integrity checks for the committed artifacts.

Verifies that the seven generated deliverables at repo root parse and match the
operational baselines, and that the two structural guarantees the decisions rest
on still hold: no malformed IRI in a CDISC namespace (docs/known-gaps.md 1a), and
nothing but the ontology and its version in the w3id namespace (decision D7).

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
import sys

from rdflib import BNode, Graph, URIRef
from rdflib.namespace import OWL, RDF, SH

BC_NS = "https://www.cdisc.org/cosmos/biomedical_concept_v1.0"
SDTM_NS = "https://www.cdisc.org/cosmos/sdtm_v1.0"
W3ID = "https://w3id.org/cdisc/cosmos/"
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
INSTANCE_TRIPLES = 29697
INSTANCE_CONCEPTS = 1469
INSTANCE_DECS = 224

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

check(f"{INSTANCES} triples", len(instances), INSTANCE_TRIPLES)
check(
    f"{INSTANCES} BiomedicalConcept nodes",
    len(set(instances.subjects(RDF.type, bc_class))),
    INSTANCE_CONCEPTS,
)
check(
    f"{INSTANCES} DataElementConcept nodes",
    len(set(instances.subjects(RDF.type, dec_class))),
    INSTANCE_DECS,
)
check(
    f"{INSTANCES} blank nodes",
    len({s for s in instances.subjects() if isinstance(s, BNode)}),
    0,
)

if failures:
    print(f"\n{len(failures)} check(s) failed: {', '.join(failures)}")
    sys.exit(1)
print("\nAll deliverable integrity checks passed.")
