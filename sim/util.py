import pyzx
import quizx
import stim

from pyzx import VertexType
from pyzx.circuit.gates import S, Z, NOT, SX, HAD, CNOT


def pyzx_to_quizx(g: pyzx.Graph) -> quizx.VecGraph:
    """Converts a pyzx graph to quizx."""
    out = quizx.VecGraph()
    v_map = dict(zip(g.vertices(), out.add_vertices(g.num_vertices()), strict=True))
    for v in g.vertices():
        out.set_type(v_map[v], g.type(v))
        out.set_phase(v_map[v], g.phase(v))
    for u, v in g.edges():
        out.add_edge((v_map[u], v_map[v]), g.edge_type((u, v)))
    out.set_inputs(tuple(v_map[v] for v in g.inputs()))
    out.set_outputs(tuple(v_map[v] for v in g.outputs()))
    out.scalar = g.scalar
    return out


def pyzx_to_stim(circ: pyzx.Circuit) -> stim.Circuit:
    """Converts pyzx circuit to stim.

    Assumes initialisation and measurement in the Z basis.
    """
    out = stim.Circuit()
    out.append("R", range(circ.qubits))
    for gate in circ:
        match gate:
            case HAD(target=tgt):
                out.append("H", tgt)
            case Z(target=tgt):
                out.append("Z", tgt)
            case NOT(target=tgt):
                out.append("X", tgt)
            case S(target=tgt, adjoint=adjoint):
                out.append("S_DAG" if adjoint else "S", tgt)
            case SX(target=tgt, adjoint=adjoint):
                out.append("SQRT_X_DAG" if adjoint else "SQRT_X", tgt)
            case CNOT(control=ctrl, target=tgt):
                out.append("CNOT", [ctrl, tgt])
            case _:
                raise NotImplementedError(gate.name)
    out.append("M", range(circ.qubits))
    return out


def compute_scalar(g: pyzx.Graph) -> pyzx.Scalar:
    """Computes the scalar for a closed pyzx graph using quizx stabilizer
    decompositions.
    """
    decomposer = quizx.Decomposer(g=pyzx_to_quizx(g), simp=quizx.SimpFunc.FullSimp)
    decomposer.decompose("BssWithCats")
    return decomposer.get_scalar()


def plug(g: pyzx.Graph, xs: list[bool]) -> None:
    """Plugs graph inputs with |0> and outputs with <xs|."""
    for v in g.inputs():
        g.set_type(v, VertexType.X)
        g.set_phase(v, 0)
    for v, x in zip(g.outputs(), xs, strict=True):
        g.set_type(v, VertexType.X)
        g.set_phase(v, x)
    g.set_inputs(())
    g.set_outputs(())
    g.scalar.add_power(-2 * len(xs))


def is_xy(pauli: int) -> bool:
    """Checks if Pauli in stim encoding is either X or Y."""
    # Stim encoding: 0=I, 1=X, 2=Y, 3=Z
    return pauli in (1, 2)


def is_yz(pauli: int) -> bool:
    """Checks if Pauli in stim encoding is either Y or Z."""
    # Stim encoding: 0=I, 1=X, 2=Y, 3=Z
    return pauli in (2, 3)
