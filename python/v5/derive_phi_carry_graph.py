#!/usr/bin/env python3
"""
IFÁ V5

Carry Transition Graph

Nodes:

    (Cin_direct, Cin_phi)

Edges:

    (Cin_direct,Cin_phi)
          |
          |  Φ-P2 block
          v
    (Cout_direct,Cout_phi)

The graph is constructed exhaustively from all
64 local carry-aware contexts.

It computes

    • reachable nodes
    • edge multiplicities
    • adjacency matrix
    • SCCs
    • cycles
    • in/out degree
"""

from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from pathlib import Path
import networkx as nx

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RESULTS = PROJECT_ROOT/"python/v5/results"

csv_file = RESULTS/"phi_p2_theorem_local_contexts.csv"

rows=[]

with csv_file.open() as f:
    reader=csv.DictReader(f)
    rows=list(reader)

graph=nx.DiGraph()

edge_counter=Counter()

for r in rows:

    src=(
        int(r["C_in"]),
        int(r["C_in_phi"])
    )

    dst=(
        int(r["C_out"]),
        int(r["C_out_phi"])
    )

    edge_counter[(src,dst)] +=1

for (u,v),w in edge_counter.items():

    graph.add_edge(
        u,
        v,
        weight=w
    )

print("="*70)
print("CARRY TRANSITION GRAPH")
print("="*70)

print()

print("Nodes :",graph.number_of_nodes())
print("Edges :",graph.number_of_edges())

print()

print("Nodes")
print("-----")

for n in sorted(graph.nodes()):

    print(
        n,
        "in",
        graph.in_degree(n),
        "out",
        graph.out_degree(n)
    )

print()

print("Edges")
print("-----")

for u,v,data in graph.edges(data=True):

    print(
        u,
        "->",
        v,
        "weight",
        data["weight"]
    )

print()

scc=list(nx.strongly_connected_components(graph))

print("Strongly Connected Components")
print("-----------------------------")

for i,c in enumerate(scc):

    print(
        i,
        sorted(c)
    )

print()

cycles=list(nx.simple_cycles(graph))

print("Cycles")
print("------")

for c in cycles:

    print(c)

adj=[]

nodes=sorted(graph.nodes())

index={
    n:i
    for i,n in enumerate(nodes)
}

matrix=[
    [0]*len(nodes)
    for _ in nodes
]

for u,v,data in graph.edges(data=True):

    matrix[
        index[u]
    ][
        index[v]
    ]=data["weight"]

adj_csv=RESULTS/"phi_carry_adjacency.csv"

with adj_csv.open(
    "w",
    newline=""
) as f:

    writer=csv.writer(f)

    writer.writerow(
        [""]+[str(n) for n in nodes]
    )

    for i,n in enumerate(nodes):

        writer.writerow(
            [str(n)]
            +matrix[i]
        )

summary={

"nodes":graph.number_of_nodes(),

"edges":graph.number_of_edges(),

"scc_count":len(scc),

"scc_sizes":[len(c) for c in scc],

"cycles":[
    [list(x) for x in c]
    for c in cycles
],

"edge_weights":{

    str(k):v
    for k,v in edge_counter.items()

}

}

summary_json=RESULTS/"phi_carry_graph_summary.json"

with summary_json.open("w") as f:

    json.dump(
        summary,
        f,
        indent=2
    )

print()

print("Saved")
print(adj_csv)
print(summary_json)

