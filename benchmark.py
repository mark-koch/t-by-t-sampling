import multiprocessing as mp
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from queue import Empty

import pyzx

import sim

TIMEOUT = 10 * 60  # Ten minutes

METHODS = {
    "qubit_by_qubit": sim.qubit_by_qubit,
    "gate_by_gate": sim.gate_by_gate,
    "t_by_t": sim.t_by_t,
}


@dataclass(unsafe_hash=True)
class Job:
    file: Path
    method: str

    @staticmethod
    def parse(s: str) -> "Job":
        [file, method, *_] = s.split(",")
        return Job(Path(file), method)

    def __str__(self) -> str:
        return f"{self.file} ({self.method})"


def get_jobs(dir: Path) -> list[Job]:
    return [Job(file, method) for file in dir.glob("**/*.qasm") for method in METHODS]


def run(job: Job, queue: mp.Queue) -> None:
    with open(job.file) as f:
        circ = pyzx.Circuit.from_qasm(f.read())
    f = METHODS[job.method]
    start = time.time()
    f(circ)
    duration = time.time() - start
    queue.put((job, duration))


if __name__ == "__main__":
    num_cores = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    with open("results.txt", "r") as f:
        done_jobs = {Job.parse(line) for line in f.readlines()}

    jobs = []
    for job in get_jobs(Path("./circuits")):
        if job in done_jobs:
            print(f"{job}: skipped")
        else:
            jobs.append(job)

    running: dict[Job, tuple[mp.Process, float]] = {}
    queue = mp.Queue()
    f = open("results.txt", "a")

    while running or jobs:
        # Start new jobs
        if jobs and len(running) < num_cores:
            job = jobs.pop()
            print(f"{job}: started")
            p = mp.Process(target=run, args=(job, queue), daemon=True)
            running[job] = (p, time.time())
            p.start()

        # Check if any jobs are done
        done = []
        for job, (p, start_time) in running.items():
            running_time = time.time() - start_time
            if p.exitcode is not None:
                p.join()
                done.append(job)
                if p.exitcode:
                    print(f"{job}: failed")
                    f.write(f"{job.file},{job.method},failed\n")
                    f.flush()
            elif running_time > TIMEOUT:
                p.kill()
                done.append(job)
                print(f"{job}: timeout")
                f.write(f"{job.file},{job.method},timeout\n")
                f.flush()
        for job in done:
            del running[job]

        # Retrieve results
        while True:
            try:
                job, duration = queue.get(block=False)
                print(f"{job}: {duration}")
                f.write(f"{job.file},{job.method},{duration}\n")
                f.flush()
            except Empty:
                break

        time.sleep(0.01)

    queue.close()
    f.close()
