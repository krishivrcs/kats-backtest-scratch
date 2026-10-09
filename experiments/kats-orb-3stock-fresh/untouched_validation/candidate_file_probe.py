#!/usr/bin/env python3
"""Second-stage file and small-archive probe for public Kaggle candidates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import urllib.request
import zipfile
from pathlib import Path

CANDIDATES = (
    "debashis74017/nifty-50-minute-data",
    "tomtillo/nse-nifty50-index-daily-minute-level-data",
    "pariminikhil/nifty-option-chain-3-oct-24-to-24-mar-26",
    "djjain21/nse-bse-and-mcx-f-and-o-historical-data-1-min-and-tick",
    "abhishekkumarphysics/correlation-between-price-change-of-stocks",
    "sumansarkar24/nifty-bank-1-minute-data-from-10-years",
)
SMALL_AMBIGUOUS = {
    "djjain21/nse-bse-and-mcx-f-and-o-historical-data-1-min-and-tick",
    "abhishekkumarphysics/correlation-between-price-change-of-stocks",
}


def request(url: str):
    return urllib.request.Request(url, headers={"User-Agent": "KATS-research-file-probe/1.0"})


def get_json(url: str):
    with urllib.request.urlopen(request(url), timeout=90) as response:
        return json.load(response)


def download(url: str, path: Path):
    with urllib.request.urlopen(request(url), timeout=180) as response, path.open("wb") as handle:
        while block := response.read(1024 * 1024):
            handle.write(block)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""): h.update(block)
    return h.hexdigest()


def inspect_archive(path: Path) -> dict:
    result = {"bytes": path.stat().st_size, "sha256": digest(path), "zip": zipfile.is_zipfile(path)}
    if not result["zip"]:
        return result
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        result["members"] = names[:500]
        result["member_count"] = len(names)
        samples = []
        for name in names:
            if name.lower().endswith((".csv", ".txt")):
                with zf.open(name) as raw:
                    samples.append({"member": name, "first_lines": raw.read(4096).decode("utf-8-sig", errors="replace").splitlines()[:3]})
                if len(samples) >= 20: break
        result["text_samples"] = samples
    return result


def files_from_payload(value) -> list[dict]:
    if isinstance(value, list): return value
    if isinstance(value, dict):
        for key in ("datasetFiles", "files", "resources"):
            if isinstance(value.get(key), list): return value[key]
    return []


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(); args.out.mkdir(parents=True, exist_ok=True)
    rows, archives = [], {}
    for ref in CANDIDATES:
        owner, slug = ref.split("/", 1)
        try:
            payload = get_json(f"https://www.kaggle.com/api/v1/datasets/list/{owner}/{slug}")
            files = files_from_payload(payload)
            if not files and isinstance(payload, dict):
                # Preserve non-sensitive response keys for diagnosing API-shape changes.
                files = [{"name": f"API_KEYS:{','.join(sorted(payload))}", "totalBytes": 0}]
            for item in files:
                rows.append({"reference": ref, "file": item.get("name") or item.get("path"),
                             "bytes": item.get("totalBytes") or item.get("size"),
                             "creation_date": item.get("creationDate")})
        except Exception as error:
            rows.append({"reference": ref, "file": "API_ERROR", "error": repr(error)})
        if ref in SMALL_AMBIGUOUS:
            path = args.out / (owner + "__" + slug + ".zip")
            try:
                download(f"https://www.kaggle.com/api/v1/datasets/download/{owner}/{slug}", path)
                archives[ref] = inspect_archive(path)
                path.unlink()
            except Exception as error:
                archives[ref] = {"download_error": repr(error)}
    fields = sorted({key for row in rows for key in row})
    with (args.out / "candidate_files.csv").open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields); writer.writeheader(); writer.writerows(rows)
    result = {"candidates": CANDIDATES, "file_rows": len(rows), "small_archive_inspection": archives,
              "pnl_calculated": False}
    (args.out / "candidate_file_probe.json").write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    print(json.dumps({"file_rows": len(rows), "archives": {key: {k: v for k, v in value.items() if k != 'members' and k != 'text_samples'} for key, value in archives.items()}}, indent=2))
    return 0


if __name__ == "__main__": raise SystemExit(main())

