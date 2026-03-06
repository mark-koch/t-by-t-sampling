import pyzx
import random

from pyzx import VertexType

from sim.util import compute_scalar


def qubit_by_qubit(circ: pyzx.Circuit) -> list[bool]:
    g = circ.to_graph()
    for v in g.inputs():
        g.set_type(v, VertexType.X)
        g.set_phase(v, 0)
    g.scalar.add_power(-len(g.inputs()))
    g.set_inputs(())

    xs = []
    prev_p = 1
    for v in g.outputs():
        g.set_type(v, VertexType.X)
        g.set_phase(v, 1)
        g.scalar.add_power(-1)
        g.set_outputs(tuple(g.outputs()[1:]))

        p_true = float(compute_scalar(g.adjoint() * g)) / prev_p
        val = random.random() < p_true
        xs.append(val)
        prev_p *= p_true if val else 1 - p_true
        if not val:
            g.set_phase(v, 0)
    return xs
