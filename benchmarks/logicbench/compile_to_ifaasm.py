import json
from pathlib import Path


def graph_to_ifaasm(graph):
    lines = []

    lines.append("; LogicBench → Ifá Assembly")
    lines.append(f"; source: {graph['source_lir']}")
    lines.append(f"; axiom: {graph['axiom']}")
    lines.append("")

    # Declare symbols
    for node in graph["nodes"]:
        lines.append(f"SYM {node['id']} ; {node['label']}")

    lines.append("")

    # Encode rules
    for edge in graph["edges"]:
        if edge["relation"] == "implies":
            lines.append(
                f"RULE_IMP {edge['source']} {edge['target']} ; {edge['source']} -> {edge['target']}"
            )

    lines.append("")

    # Encode facts
    for fact in graph["facts"]:
        if fact["truth"]:
            lines.append(f"FACT {fact['symbol']}")
        else:
            lines.append(f"FACT_NOT {fact['symbol']}")

    lines.append("")

    # Axiom-specific inference
    if graph["axiom"] == "modus_tollens":
        rule = graph["edges"][0]
        lines.append(f"INFER_MT {rule['source']} {rule['target']}")
    else:
        lines.append(f"; TODO unsupported axiom: {graph['axiom']}")

    # Query / assertion
    q = graph["query"]
    if q["truth"]:
        lines.append(f"ASSERT {q['symbol']}")
    else:
        lines.append(f"ASSERT_NOT {q['symbol']}")

    lines.append("PRINT")
    lines.append("HALT")

    return "\n".join(lines)


if __name__ == "__main__":
    in_path = Path("benchmarks/logicbench/graph_modus_tollens_1.json")
    graph = json.loads(in_path.read_text(encoding="utf-8"))

    asm = graph_to_ifaasm(graph)

    print(asm)

    out = Path("benchmarks/logicbench/modus_tollens_1.ifaasm")
    out.write_text(asm, encoding="utf-8")

    print()
    print(f"Saved: {out}")
