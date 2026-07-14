import json
from pathlib import Path


def lir_to_relation_graph(lir):
    nodes = []
    edges = []

    for sym, label in lir["symbols"].items():
        nodes.append({
            "id": sym,
            "label": label,
            "type": "symbol"
        })

    for rule in lir["rules"]:
        if rule["type"] == "implies":
            edges.append({
                "id": rule["id"],
                "source": rule["if"],
                "target": rule["then"],
                "relation": "implies"
            })

    facts = lir.get("facts", [])
    query = lir.get("query", {})

    graph = {
        "graph_version": "0.1",
        "source_lir": lir["id"],
        "axiom": lir["axiom"],
        "nodes": nodes,
        "edges": edges,
        "facts": facts,
        "query": query,
        "expected": lir["expected"]
    }

    return graph


if __name__ == "__main__":
    in_path = Path("benchmarks/logicbench/lir_modus_tollens_1.json")
    lir = json.loads(in_path.read_text(encoding="utf-8"))

    graph = lir_to_relation_graph(lir)

    print(json.dumps(graph, indent=2, ensure_ascii=False))

    out = Path("benchmarks/logicbench/graph_modus_tollens_1.json")
    out.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")

    print()
    print(f"Saved: {out}")
