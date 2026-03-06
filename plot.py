from collections import defaultdict
from pathlib import Path

from matplotlib import pyplot as plt

COLORS = {
    "qubit_by_qubit": "tab:blue",
    "gate_by_gate": "tab:orange",
    "t_by_t": "tab:green",
}
LABELS = {
    "qubit_by_qubit": "qubit-by-qubit",
    "gate_by_gate": "gate-by-gate",
    "t_by_t": "T-by-T",
}


def parse_results(
    lines: list[str], task: str
) -> dict[str, defaultdict[int, float | None]]:
    results = {
        "qubit_by_qubit": defaultdict(list),
        "gate_by_gate": defaultdict(list),
        "t_by_t": defaultdict(list),
    }
    for line in lines:
        file, method, time = line.split(",")
        if task in file:
            file = Path(file)
            [x, *_] = file.stem.split("-")
            t = float("infinity") if time.startswith("timeout") else float(time)
            results[method][int(x)].append(t)
    return results


def plot_avgs(
    results: dict[str, defaultdict[int, float | None]],
    x_label: str,
    log=False,
    x_ticks=None,
    legend: str = "",
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(4.5, 3))
    plt.xlabel(x_label)
    plt.ylabel("Sample time (seconds)")
    ax.grid(True, alpha=0.2)
    if log:
        ax.set_yscale("log", base=10)
    if x_ticks:
        ax.xaxis.set_ticks(x_ticks)

    for method, values in results.items():
        xys = [
            (x, timing)
            for x, timinings in values.items()
            if x < 160
            for timing in timinings
        ]
        xys.sort()
        plt.scatter(
            [x for x, _ in xys],
            [y for _, y in xys],
            marker=".",
            s=20,
            alpha=0.3,
            color=COLORS[method],
        )

        timeouts = [x for x, y in xys if y == float("infinity")]
        plt.scatter(
            timeouts,
            [600 for _ in timeouts],
            marker="x",
            s=20,
            alpha=0.3,
            color=COLORS[method],
        )

        avgs = []
        for x, timings in values.items():
            if x >= 160:
                continue
            ys = [y for y in timings if y != float("infinity")]
            if len(timings) - len(ys) > 2:
                continue
            avgs.append((x, sum(ys) / len(ys)))
        avgs.sort()
        plt.plot(
            [x for x, _ in avgs],
            [y for _, y in avgs],
            color=COLORS[method],
            label=LABELS[method],
        )

    if legend:
        plt.legend(
            loc=legend,
            shadow=False,
            fancybox=False,
            framealpha=1,
            facecolor="white",
            edgecolor="black",
        )
    plt.tight_layout()
    return fig


def plot_single(
    results: dict[str, defaultdict[int, float | None]],
    x_label: str,
    log=False,
    x_ticks=None,
    legend: str = "",
) -> plt.Figure:
    fig, ax = plt.subplots(figsize=(4.5, 3))
    plt.xlabel(x_label)
    plt.ylabel("Sample time (seconds)")
    ax.grid(True, alpha=0.2)
    if log:
        ax.set_yscale("log", base=10)
    if x_ticks:
        ax.xaxis.set_ticks(x_ticks)

    for method, values in results.items():
        xys = [(x, timing) for x, [timing, *_] in values.items()]
        xys.sort()
        plt.plot(
            [x for x, _ in xys],
            [y for _, y in xys],
            marker=".",
            color=COLORS[method],
            label=LABELS[method],
        )

        timeouts = [x for x, y in xys if y == float("infinity")]
        plt.scatter(
            timeouts, [600 for _ in timeouts], marker="x", s=20, color=COLORS[method]
        )

    if legend:
        plt.legend(
            loc=legend,
            shadow=False,
            fancybox=False,
            framealpha=1,
            facecolor="white",
            edgecolor="black",
        )
    plt.tight_layout()
    return fig


if __name__ == "__main__":
    plt.rcParams.update(
        {
            "text.usetex": True,
            "font.family": "serif",
            "font.serif": ["Times"],
            "font.size": 11,
            "pgf.texsystem": "pdflatex",
        }
    )

    with open("results.txt") as f:
        lines = f.readlines()

    plots_dir = Path("./plots")
    plots_dir.mkdir(exist_ok=True)

    plot_avgs(
        results=parse_results(lines, "pauliexp_layers"),
        x_label="T-count",
        x_ticks=range(10, 51, 5),
    ).savefig(plots_dir / "pauliexp_layers.pdf", bbox_inches="tight")

    plot_avgs(
        results=parse_results(lines, "pauliexp_layers"),
        x_label="T-count",
        x_ticks=range(10, 51, 5),
        log=True,
        legend="lower right",
    ).savefig(plots_dir / "pauliexp_layers_log.pdf", bbox_inches="tight")

    plot_avgs(
        results=parse_results(lines, "pauliexp_qubits"),
        x_label="Qubits",
        x_ticks=range(10, 151, 20),
    ).savefig(plots_dir / "pauliexp_qubits.pdf", bbox_inches="tight")

    plot_avgs(
        results=parse_results(lines, "pauliexp_qubits"),
        x_label="Qubits",
        x_ticks=range(10, 151, 20),
        log=True,
        legend="lower right",
    ).savefig(plots_dir / "pauliexp_qubits_log.pdf", bbox_inches="tight")

    plot_single(
        results=parse_results(lines, "cultiv_distance"),
        x_label="Escape distance",
        x_ticks=range(7, 20, 2),
    ).savefig(plots_dir / "cultiv_distance.pdf", bbox_inches="tight")

    plot_single(
        results=parse_results(lines, "cultiv_distance"),
        x_label="Escape distance",
        x_ticks=range(7, 20, 2),
        log=True,
    ).savefig(plots_dir / "cultiv_distance_log.pdf", bbox_inches="tight")

    cultive_distance = parse_results(lines, "cultiv_distance")
    cultive_distance["qubit_by_qubit"] = {}
    cultive_distance["gate_by_gate"] = {}
    plot_single(
        results=cultive_distance,
        x_label="Escape distance",
        x_ticks=range(7, 20, 2),
        legend="upper left",
    ).savefig(plots_dir / "cultiv_distance_only_t.pdf", bbox_inches="tight")
