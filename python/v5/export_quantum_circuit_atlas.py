#!/usr/bin/env python3
"""Export the verified IFÁ V5 Qiskit circuits as text, SVG, PNG and PDF.

Run from the project root:
    python3 python/v5/export_quantum_circuit_atlas.py

Or from this extracted v5 directory:
    python3 export_quantum_circuit_atlas.py

The exporter imports the existing circuit builders. It does not reconstruct or
change any circuit, so every image is generated directly from the verified
Python/Qiskit source.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any

# --- IFÁ project import bootstrap ---
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent if SCRIPT_DIR.parent.name == "python" else SCRIPT_DIR.parent
for candidate in (PROJECT_ROOT, SCRIPT_DIR, SCRIPT_DIR.parent):
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
# -----------------------------------

try:
    from qiskit import QuantumCircuit
except ImportError as exc:
    raise SystemExit(
        "Qiskit is required. Activate the same Python environment used for the "
        "verified IFÁ quantum simulations, then rerun this exporter.\n"
        f"Original import error: {exc}"
    ) from exc


def _import_builders() -> dict[str, Callable[[], Any]]:
    """Support both project-package and standalone extracted-directory use."""
    try:
        from python.v5.simulate_phi_p2_qiskit import build_phi_p2_gate
        from python.v5.simulate_phi_p8_qiskit import build_phi_p8_circuit
        from python.v5.simulate_relation_frame_qiskit import (
            build_local_relation_cell,
            build_relation_frame_circuit,
        )
        from python.v5.simulate_quantum_full_adder import build_quantum_full_adder
        from python.v5.simulate_quantum_dual_carry_ripple_4bit import build_dual_carry_ripple
        from python.v5.ifa_quantum_processor import build_quantum_processor
        from python.v5.simulate_quantum_ifa_alu_integrated import build_integrated_ifa_alu
    except ModuleNotFoundError:
        from simulate_phi_p2_qiskit import build_phi_p2_gate
        from simulate_phi_p8_qiskit import build_phi_p8_circuit
        from simulate_relation_frame_qiskit import (
            build_local_relation_cell,
            build_relation_frame_circuit,
        )
        from simulate_quantum_full_adder import build_quantum_full_adder
        from simulate_quantum_dual_carry_ripple_4bit import build_dual_carry_ripple
        from ifa_quantum_processor import build_quantum_processor
        from simulate_quantum_ifa_alu_integrated import build_integrated_ifa_alu

    return {
        "phi_p2": build_phi_p2_gate,
        "phi_p8": build_phi_p8_circuit,
        "relation_cell": build_local_relation_cell,
        "relation_frame": build_relation_frame_circuit,
        "quantum_full_adder": build_quantum_full_adder,
        "dual_carry_ripple_4bit": build_dual_carry_ripple,
        "quantum_processor_8bit": build_quantum_processor,
        "integrated_quantum_alu_8bit": build_integrated_ifa_alu,
    }


@dataclass(frozen=True)
class CircuitEntry:
    slug: str
    title: str
    builder: Callable[[], Any]


def unwrap_circuit(value: Any) -> QuantumCircuit:
    """Accept builders returning either a circuit or a layout with .circuit."""
    circuit = value if isinstance(value, QuantumCircuit) else getattr(value, "circuit", None)
    if not isinstance(circuit, QuantumCircuit):
        raise TypeError(
            f"Builder returned {type(value).__name__}; expected QuantumCircuit "
            "or an object with a QuantumCircuit .circuit attribute"
        )
    return circuit


def write_text_diagram(circuit: QuantumCircuit, path: Path, fold: int) -> None:
    drawing = circuit.draw(output="text", fold=fold)
    path.write_text(str(drawing) + "\n", encoding="utf-8")


def write_matplotlib_diagram(
    circuit: QuantumCircuit,
    path: Path,
    fold: int,
    scale: float,
) -> None:
    """Draw through Qiskit's Matplotlib drawer and save by extension."""
    try:
        figure = circuit.draw(
            output="mpl",
            fold=fold,
            scale=scale,
            style={
                "backgroundcolor": "#ffffff",
                "linecolor": "#000000",
                "textcolor": "#000000",
                "gatetextcolor": "#000000",
                "gatefacecolor": "#ffffff",
                "barrierfacecolor": "#000000",
                "creglinecolor": "#000000",
            },
        )
    except ImportError as exc:
        raise RuntimeError(
            "The Matplotlib circuit drawer needs matplotlib and pylatexenc. "
            "Install them in the active environment and rerun."
        ) from exc

    figure.savefig(path, bbox_inches="tight", facecolor="white")

    # Avoid accumulating figures while exporting the large processor/ALU.
    try:
        import matplotlib.pyplot as plt
        plt.close(figure)
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "docs" / "quantum" / "circuits",
        help="Output directory (default: docs/quantum/circuits)",
    )
    parser.add_argument(
        "--formats",
        nargs="+",
        choices=("text", "svg", "png", "pdf"),
        default=("text", "svg", "png", "pdf"),
        help="Diagram formats to export",
    )
    parser.add_argument(
        "--fold",
        type=int,
        default=120,
        help="Maximum circuit width before Qiskit wraps the drawing",
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=0.70,
        help="Matplotlib circuit scale",
    )
    parser.add_argument(
        "--only",
        nargs="*",
        default=None,
        help="Optional circuit slugs to export",
    )
    args = parser.parse_args()

    builders = _import_builders()
    titles = {
        "phi_p2": "IFÁ Φ-P2",
        "phi_p8": "IFÁ Φ-P8",
        "relation_cell": "IFÁ Local Relation Cell",
        "relation_frame": "IFÁ 8-bit Relation Frame",
        "quantum_full_adder": "IFÁ Quantum Full Adder",
        "dual_carry_ripple_4bit": "IFÁ 4-bit Dual-Carry Ripple",
        "quantum_processor_8bit": "IFÁ 8-bit Quantum Processor",
        "integrated_quantum_alu_8bit": "IFÁ Integrated 8-bit Quantum ALU",
    }

    entries = [
        CircuitEntry(slug, titles[slug], builder)
        for slug, builder in builders.items()
        if args.only is None or slug in set(args.only)
    ]
    if not entries:
        parser.error("No circuits selected. Check the names passed to --only.")

    output_dir = args.output.resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest: list[dict[str, object]] = []
    failures: list[str] = []

    print("=== IFÁ QUANTUM CIRCUIT ATLAS EXPORT ===", flush=True)
    print(f"Output directory: {output_dir}", flush=True)

    for entry in entries:
        print(f"\nBuilding {entry.title} ...", flush=True)
        try:
            circuit = unwrap_circuit(entry.builder())
            files: list[str] = []

            if "text" in args.formats:
                path = output_dir / f"{entry.slug}.txt"
                write_text_diagram(circuit, path, args.fold)
                files.append(path.name)
                print(f"  wrote {path.name}", flush=True)

            for fmt in ("svg", "png", "pdf"):
                if fmt not in args.formats:
                    continue
                path = output_dir / f"{entry.slug}.{fmt}"
                write_matplotlib_diagram(circuit, path, args.fold, args.scale)
                files.append(path.name)
                print(f"  wrote {path.name}", flush=True)

            manifest.append(
                {
                    "slug": entry.slug,
                    "title": entry.title,
                    "circuit_name": circuit.name,
                    "qubits": circuit.num_qubits,
                    "clbits": circuit.num_clbits,
                    "depth": circuit.depth(),
                    "size": circuit.size(),
                    "operations": dict(circuit.count_ops()),
                    "files": files,
                }
            )
        except Exception as exc:
            message = f"{entry.slug}: {type(exc).__name__}: {exc}"
            failures.append(message)
            print(f"  ERROR: {message}", file=sys.stderr, flush=True)

    manifest_path = output_dir / "circuit_atlas_manifest.json"
    manifest_path.write_text(
        json.dumps(
            {
                "atlas": "IFÁ Quantum Circuit Atlas",
                "generated_from_verified_builders": True,
                "circuits": manifest,
                "failures": failures,
            },
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    print(f"\nManifest: {manifest_path}", flush=True)
    print(f"Circuits exported: {len(manifest)}", flush=True)
    print(f"Failures: {len(failures)}", flush=True)
    print("RESULT: " + ("PASS" if not failures else "FAIL"), flush=True)
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
