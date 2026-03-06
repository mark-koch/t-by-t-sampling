import pyzx
import random

from pyzx.circuit.gates import T, S, Z, SX, NOT, HAD, CNOT

from sim.util import compute_scalar, plug


def gate_by_gate(circ: pyzx.Circuit) -> list[bool]:
    xs = [False] * circ.qubits
    prefix = pyzx.Circuit(circ.qubits)
    for gate in circ:
        prefix += gate
        match gate:
            case T() | S() | Z():
                pass
            case NOT(target=tgt):
                xs[tgt] ^= 1
            case CNOT(control=ctrl, target=tgt):
                xs[tgt] ^= xs[ctrl]
            case HAD(target=tgt) | SX(target=tgt):
                g = prefix.to_graph()
                v_tgt = g.outputs()[tgt]
                plug(g, xs)

                g.set_phase(v_tgt, 0)
                s0 = compute_scalar(g)
                a0 = float(s0 * s0.conjugate())

                g.set_phase(v_tgt, 1)
                s1 = compute_scalar(g)
                a1 = float(s1 * s1.conjugate())

                p_true = a1 / (a0 + a1)
                xs[tgt] = random.random() < p_true
            case _:
                raise NotImplementedError(gate.name)
    return xs
