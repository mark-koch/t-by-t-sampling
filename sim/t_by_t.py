import random

import pyzx
import stim

from pyzx.circuit.gates import T, S, Z, NOT, SX, HAD, CNOT

from sim.util import pyzx_to_stim, plug, is_xy, compute_scalar


def mbqcify_ts(circ: pyzx.Circuit) -> tuple[pyzx.Circuit, list[T]]:
    """Builds a new circuit where Ts are replaced with MBQC wires."""
    out = pyzx.Circuit(circ.qubits + circ.tcount())
    ts = []
    for gate in circ:
        if isinstance(gate, T):
            out.add_gate("CNOT", gate.target, circ.qubits + len(ts))
            ts.append(gate)
        else:
            out.add_gate(gate)
    return out, ts


def mbqcify_ts_stim(circ: pyzx.Circuit) -> stim.Circuit:
    """Equivalent to `pyzx_to_stim(mbqcify_ts(ts))`, however remembers which
    CNOTs correspond to Ts.

    Also skips initial resets and final measurements.
    """
    out = stim.Circuit()
    next_qubit = circ.qubits
    for gate in circ:
        match gate:
            case HAD(target=tgt):
                out.append("H", tgt)
            case NOT(target=tgt):
                out.append("X", tgt)
            case Z(target=tgt):
                out.append("Z", tgt)
            case S(target=tgt, adjoint=adjoint):
                out.append("S_DAG" if adjoint else "S", tgt)
            case SX(target=tgt, adjoint=adjoint):
                out.append("SQRT_X_DAG" if adjoint else "SQRT_X", tgt)
            case CNOT(control=ctrl, target=tgt):
                out.append("CNOT", [ctrl, tgt])
            case T(target=tgt):
                out.append("TICK")
                out.append("CNOT", [tgt, next_qubit], tag="T")
                out.append("TICK")
                next_qubit += 1
            case _:
                raise NotImplementedError(gate.name)
    return out


def get_corrections(circ: pyzx.Circuit) -> list[stim.PauliString]:
    """For each T gate, computes the forward corrections that need to be
    applied when the MBQC measurement fails.
    """
    corrections = []
    stim_circ = mbqcify_ts_stim(circ)
    for i, inst in enumerate(stim_circ):
        if inst.tag == "T":
            [tgt, _] = inst.targets_copy()
            z = stim.PauliString(stim_circ.num_qubits)
            z[tgt.qubit_value] = "Z"
            corrections.append(z.after(stim_circ[i:]))
    # Sanity check: Corrections don't push into the past
    for i, corr in enumerate(corrections):
        assert not any(corr[circ.qubits : circ.qubits + i + 1])
    return corrections


def t_by_t(circ: pyzx.Circuit) -> list[bool]:
    mbqc_circ, ts = mbqcify_ts(circ)
    stim_circ = pyzx_to_stim(mbqc_circ)
    corrections = get_corrections(circ)

    # Get initial sample from stim
    xs = [bool(x) for x in stim_circ.compile_sampler().sample(1)[0]]

    for t_idx, t_gate in enumerate(ts):
        tgt = circ.qubits + t_idx
        mbqc_circ.add_gate(T(tgt, t_gate.adjoint))
        mbqc_circ.add_gate("H", tgt)

        g = mbqc_circ.to_graph()
        v_tgt = g.outputs()[tgt]
        plug(g, xs)

        g.set_phase(v_tgt, 0)
        s0 = compute_scalar(g)
        a0 = float(s0 * s0.conjugate())
        g.set_phase(v_tgt, 1)
        s1 = compute_scalar(g)
        a1 = float(s1 * s1.conjugate())
        p_true = a1 / (a0 + a1)

        if random.random() < p_true:
            # We sampled outcome 1, so we need to apply the corresponding correction
            for j, corr in enumerate(corrections[t_idx]):
                xs[j] ^= is_xy(corr)

        # After the potential correction, the outcome is definitely 0
        xs[tgt] = False

    return xs[: circ.qubits]


if __name__ == "__main__":
    circ = pyzx.Circuit.from_qasm_file("../circuits/cultiv_distance/7.qasm")
    print(t_by_t(circ))
