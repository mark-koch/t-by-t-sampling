# T-by-T Sampling for Clifford+T Quantum Circuits

Implementations of the different sampling algorithms can be found in the `./sim` directory.

## Setup

Install the [uv Python package manager](https://docs.astral.sh/uv/getting-started/installation/) and run `uv sync` to install all dependencies.

## Benchmarks

Benchmarking circuits are included in the `./circuits` directory and can be regenrated by running `uv run generate_circuits.py`.

To run the benchmarks, first delete the `results.txt` file and then run `uv run benchmark.py`.
To distribute the workload across multiple CPU cores, pass the number of processes to be used as a command line argument.
For example, `uv run benchmark.py 8` will distribute the benchmark across 8 cores.
Running the benchmarks should take a couple of hours.

To plot the final results, run `uv run plot.py`.
Note that this requires `pdflatex` to be in the system path.
The final plots can be found in the `./plots` directory.
