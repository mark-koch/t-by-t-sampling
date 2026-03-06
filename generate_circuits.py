import sys

sys.path.append("./cultivation")

from pathlib import Path
from pyzx.circuit.gates import T, HAD

import pyzx
import random
import stim

import cultiv


def random_pauli_exponential(qubits: int, layers: int) -> pyzx.Circuit:
    circ = pyzx.Circuit(qubits)
    for _ in range(layers):
        paulis = random.choices(["I", "X", "Y", "Z"], k=qubits)
        targets = [i for i, p in enumerate(paulis) if p != "I"]

        # Basis change
        for tgt, p in zip(targets, paulis):
            if p == "X":
                circ.add_gate("HAD", tgt)
            elif p == "Y":
                circ.add_gate("SX", tgt)

        # Ladder
        for ctrl in targets[:-1]:
            circ.add_gate("CNOT", ctrl, targets[-1])
        circ.add_gate("T", targets[-1])
        for ctrl in targets[:-1]:
            circ.add_gate("CNOT", ctrl, targets[-1])

        # Basis change
        for tgt, p in zip(targets, paulis):
            if p == "X":
                circ.add_gate("HAD", tgt)
            elif p == "Y":
                circ.add_gate(pyzx.gates.SX(tgt, adjoint=True))
    return circ


def stim_to_pyzx(circ: stim.Circuit) -> pyzx.Circuit:
    out = pyzx.Circuit(0)
    mapping = {}

    def add_qubit() -> int:
        out.qubits += 1
        return out.qubits - 1

    for inst in circ:
        targets = inst.targets_copy()
        match inst.name:
            case "R" | "RX" as name:
                for t in targets:
                    q = t.qubit_value
                    mapping[q] = add_qubit()
                    if "X" in name:
                        out.add_gate("H", mapping[q])
            case "M" | "MX" as name:
                for t in targets:
                    q = t.qubit_value
                    if "X" in name:
                        out.add_gate("H", mapping[q])
            case "CX":
                for src, tgt in inst.target_groups():
                    src = src.qubit_value
                    tgt = tgt.qubit_value
                    out.add_gate("CNOT", mapping[src], mapping[tgt])
            case "S" | "S_DAG" as name:
                for t in targets:
                    q = t.qubit_value
                    out.add_gate(T(mapping[q], adjoint="DAG" in name))
            case (
                "TICK"
                | "QUBIT_COORDS"
                | "TICK"
                | "MPP"
                | "DETECTOR"
                | "OBSERVABLE_INCLUDE"
            ):
                pass
            case name:
                raise NotImplementedError(name)
    return out


if __name__ == "__main__":
    random.seed(0)
    root = Path("./circuits")
    root.mkdir(exist_ok=True)

    pauliexp_layers = root / "pauliexp_layers"
    pauliexp_layers.mkdir(exist_ok=True)
    for layers in range(10, 50, 3):
        for i in range(10):
            circ = random_pauli_exponential(qubits=50, layers=layers)
            with open(pauliexp_layers / f"{layers}-{i}.qasm", "w") as f:
                f.write(circ.to_qasm())

    pauliexp_qubits = root / "pauliexp_qubits"
    pauliexp_qubits.mkdir(exist_ok=True)
    for qubits in range(10, 151, 10):
        for i in range(10):
            circ = random_pauli_exponential(qubits=qubits, layers=30)
            with open(pauliexp_qubits / f"{qubits}-{i}.qasm", "w") as f:
                f.write(circ.to_qasm())

    cultiv_distance = root / "cultiv_distance"
    cultiv_distance.mkdir(exist_ok=True)
    for d in range(7, 20, 2):
        stim_circ = cultiv.make_end2end_cultivation_circuit(
            dcolor=3,
            dsurface=d,
            basis="Y",
            r_growing=3,
            r_end=5,
            inject_style="unitary",
        ).flattened()
        circ = stim_to_pyzx(stim_circ)
        with open(cultiv_distance / f"{d}.qasm", "w") as f:
            f.write(circ.to_qasm())

        # Log circuit stats
        tcount = len([g for g in circ.gates if isinstance(g, T)])
        hcount = len([g for g in circ.gates if isinstance(g, HAD)])
        print(
            f"d={d}, qubits={stim_circ.num_qubits}, gates={len(circ.gates)}, "
            f"measurements={stim_circ.num_measurements}, hcount={hcount}, "
            f"tcount={tcount}"
        )
