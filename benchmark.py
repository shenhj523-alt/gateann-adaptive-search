"""Compare fixed and adaptive GateANN budgets with the course's YFCC workloads."""

import argparse
import csv
import os
from pathlib import Path
import re
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--binary", type=Path, required=True)
    parser.add_argument("--index-prefix", type=Path, required=True)
    parser.add_argument("--dataset", type=Path, required=True, help="Formal dataset directory")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--rounds", type=int, default=3)
    parser.add_argument("--buckets", nargs="+", choices=("low", "medium", "high"),
                        default=["low", "medium", "high"])
    args = parser.parse_args()
    if args.rounds < 1:
        parser.error("--rounds must be positive")

    args.output.mkdir(parents=True, exist_ok=False)
    variants = (("fixed320", 320, "0"), ("adaptive", 320, "1"), ("fixed640", 640, "0"))
    columns = ("round", "bucket", "variant", "queries", "recall_percent",
               "mean_latency_us", "mean_ios", "filter_skips", "expanded", "at_cap")
    with (args.output / "results.csv").open("w", newline="", encoding="utf-8") as result:
        writer = csv.writer(result)
        writer.writerow(columns)
        for round_id in range(args.rounds):
            order = variants[round_id % 3:] + variants[:round_id % 3]
            for bucket in args.buckets:
                workload = args.dataset / "workloads" / bucket
                for variant, budget, adaptive in order:
                    command = [
                        args.binary.resolve(), "uint8", args.index_prefix.resolve(), "1", "8",
                        workload / "query.u8bin", args.dataset / "base.metadata.spmat",
                        workload / "query.metadata.spmat", workload / "ground_truth.ids.ibin",
                        "10", "l2", "pq", "8", "0", "0", "32", str(budget),
                    ]
                    name = f"{round_id + 1}-{bucket}-{variant}"
                    print(name, flush=True)
                    run = subprocess.run(command, env={**os.environ, "GATEANN_ADAPTIVE_L": adaptive},
                                         stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                    (args.output / f"{name}.log").write_text(run.stdout, encoding="utf-8")
                    run.check_returncode()
                    data = next(line.split() for line in run.stdout.splitlines()
                                if re.fullmatch(rf"\s*{budget}(?:\s+[-+]?\d+(?:\.\d+)?){{7}}\s*", line))
                    metrics = dict(re.findall(r"(\w+)=([\d.]+)",
                                              next(line for line in run.stdout.splitlines()
                                                   if line.startswith("GateANN metrics "))))
                    writer.writerow([round_id + 1, bucket, variant, metrics["queries"],
                                     f"{float(data[2]) * 100:.2f}", metrics["mean_latency_us"],
                                     data[3], data[4], metrics["expanded"], metrics["at_cap"]])
                    result.flush()


if __name__ == "__main__":
    main()
