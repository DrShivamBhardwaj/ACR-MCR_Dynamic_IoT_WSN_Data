from pathlib import Path
import json
import pandas as pd

ROOT = Path(__file__).resolve().parent
raw = pd.read_csv(ROOT / "results" / "raw_results.csv")
manifest = json.loads((ROOT / "results" / "manifest.json").read_text())
verification = json.loads((ROOT / "verification.json").read_text())

main = raw[raw["group"].eq("main")]
checks = {
    "outcome_runs": int(len(raw)),
    "primary_runs": int(len(main)),
    "primary_seeds": int(main["seed"].nunique()),
    "primary_scenarios": int(main["scenario"].nunique()),
    "primary_methods": int(main["method"].nunique()),
    "timing_runs": int(len(pd.read_csv(ROOT / "analysis" / "timing_profile.csv"))),
    "raw_round_files": len(list((ROOT / "results" / "rounds").glob("*.csv.gz"))),
    "diagnostic_link_files": len(list((ROOT / "results" / "links").glob("*.csv.gz"))),
    "verified_mechanisms": int(sum(bool(v) for v in verification.values())),
    "manifest_job_count": int(manifest.get("job_count", -1)),
}
expected = {
    "outcome_runs": 1280, "primary_runs": 1050, "primary_seeds": 30,
    "primary_scenarios": 5, "primary_methods": 7, "timing_runs": 30,
    "raw_round_files": 1280, "diagnostic_link_files": 35,
    "verified_mechanisms": 13, "manifest_job_count": 1280,
}
checks["all_release_counts_match"] = all(checks[k] == v for k, v in expected.items())
print(json.dumps(checks, indent=2))
if not checks["all_release_counts_match"]:
    raise SystemExit(1)
