from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import reversal


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        path.write_text("\n", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def save_partition(out: Path, name: str, candidates, trades, rejects) -> dict[str, object]:
    write_csv(out / f"{name}_candidates.csv", [reversal.candidate_dict(item) for item in candidates])
    write_csv(out / f"{name}_trades.csv", trades)
    write_csv(out / f"{name}_rejections.csv", rejects)
    return reversal.infra.metrics(trades)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(); args.out.mkdir(parents=True, exist_ok=True)

    dev_data, dev_manifest, dev_exclusions = reversal.load_until(args.archive, reversal.DEV_END)
    dev_candidates = reversal.generate_candidates(dev_data, reversal.DEV_START, reversal.DEV_END)
    dev_trades, dev_rejects = reversal.run_portfolio(dev_data, dev_candidates, 5.0)
    dev_adverse_trades, dev_adverse_rejects = reversal.run_portfolio(dev_data, dev_candidates, 10.0)
    development = save_partition(args.out, "development", dev_candidates, dev_trades, dev_rejects)
    development_adverse = save_partition(args.out, "development_adverse", dev_candidates, dev_adverse_trades, dev_adverse_rejects)
    write_csv(args.out / "development_source_exclusions.csv", dev_exclusions)
    (args.out / "development_manifest.json").write_text(json.dumps(dev_manifest, indent=2, sort_keys=True) + "\n")

    result: dict[str, object] = {
        "strategy": "KATS-FAILED-BREAKOUT-VWAP-LONG-V1",
        "development_signals": len(dev_candidates), "development": development,
        "development_adverse": development_adverse,
        "development_gate": "PASS" if reversal.development_pass(development, development_adverse) else "FAIL",
        "validation_status": "NOT_ACCESSED_DEVELOPMENT_GATE_FAILED",
        "validation": None, "validation_adverse": None,
        "paper_engine_status": "NOT_IMPLEMENTED",
    }

    if result["development_gate"] == "FAIL":
        result["verdict"] = "REJECT_DEVELOPMENT"
    else:
        val_data, val_manifest, val_exclusions = reversal.load_until(args.archive, reversal.VAL_END)
        val_candidates = reversal.generate_candidates(val_data, reversal.VAL_START, reversal.VAL_END)
        val_trades, val_rejects = reversal.run_portfolio(val_data, val_candidates, 5.0)
        val_adverse_trades, val_adverse_rejects = reversal.run_portfolio(val_data, val_candidates, 10.0)
        validation = save_partition(args.out, "validation", val_candidates, val_trades, val_rejects)
        validation_adverse = save_partition(args.out, "validation_adverse", val_candidates, val_adverse_trades, val_adverse_rejects)
        write_csv(args.out / "validation_source_exclusions.csv", val_exclusions)
        (args.out / "validation_manifest.json").write_text(json.dumps(val_manifest, indent=2, sort_keys=True) + "\n")
        result.update({"validation_status": "ACCESSED_AFTER_DEVELOPMENT_PASS", "validation_signals": len(val_candidates),
                       "validation": validation, "validation_adverse": validation_adverse})
        if reversal.validation_pass(validation, validation_adverse, development["trades"]):
            result["verdict"] = "VALIDATED_CANDIDATE_REQUIRES_INDEPENDENT_REVIEW"
            result["paper_engine_status"] = "BLOCKED_PENDING_INDEPENDENT_REVIEW"
        else:
            result["verdict"] = "REJECT_VALIDATION"

    (args.out / "results.json").write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps(result, sort_keys=True, allow_nan=False))


if __name__ == "__main__":
    main()

