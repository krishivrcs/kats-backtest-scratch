from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from engine import (DEV_END, DEV_START, VAL_END, VAL_START, candidate_dict,
                    generate_candidates, load_archive, metrics, run_portfolio,
                    validation_pass)


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)

    data, manifest, exclusions = load_archive(args.archive)
    dev_candidates = generate_candidates(data, DEV_START, DEV_END)
    val_candidates = generate_candidates(data, VAL_START, VAL_END)
    dev_trades, dev_rejects = run_portfolio(data, dev_candidates, 5.0)
    val_trades, val_rejects = run_portfolio(data, val_candidates, 5.0)
    adverse_trades, adverse_rejects = run_portfolio(data, val_candidates, 10.0)
    result = {
        "strategy": "KATS-5EMA-CASH-LONG-SPRINT-V1",
        "data_source": manifest,
        "periods": {"development": [str(DEV_START), str(DEV_END)], "validation": [str(VAL_START), str(VAL_END)]},
        "development_candidates": len(dev_candidates), "validation_candidates": len(val_candidates),
        "development": metrics(dev_trades), "validation": metrics(val_trades),
        "adverse_validation": metrics(adverse_trades),
    }
    passed = validation_pass(result["validation"], result["adverse_validation"])
    result["verdict"] = "VALIDATED_CANDIDATE" if passed else "REJECT"
    result["paper_engine_status"] = "REQUIRED_NEXT_COMMIT" if passed else "NOT_IMPLEMENTED_VALIDATION_FAILED"

    (args.out / "data_manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    (args.out / "results.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    write_csv(args.out / "source_exclusions.csv", exclusions)
    write_csv(args.out / "development_candidates.csv", [candidate_dict(c) for c in dev_candidates])
    write_csv(args.out / "validation_candidates.csv", [candidate_dict(c) for c in val_candidates])
    write_csv(args.out / "development_trades.csv", dev_trades)
    write_csv(args.out / "validation_trades.csv", val_trades)
    write_csv(args.out / "adverse_validation_trades.csv", adverse_trades)
    write_csv(args.out / "development_rejections.csv", dev_rejects)
    write_csv(args.out / "validation_rejections.csv", val_rejects)
    write_csv(args.out / "adverse_validation_rejections.csv", adverse_rejects)
    print(json.dumps({
        "strategy": result["strategy"], "development": result["development"],
        "validation": result["validation"], "adverse_validation": result["adverse_validation"],
        "verdict": result["verdict"], "paper_engine_status": result["paper_engine_status"],
    }, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()

