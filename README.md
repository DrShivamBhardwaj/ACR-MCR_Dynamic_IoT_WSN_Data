# ACR-MCR Dynamic IoT WSN — Data and Reproducibility

This repository contains the simulation code, experimental protocol, raw and derived outputs, statistical analyses, verification checks, and figure-generation sources supporting the study:

**Adaptive Conformal Clustering and Routing in Dynamic IoT Sensor Networks Under Explicit Telemetry Costs**

Authors: Shivam Bhardwaj, Jitendra Nath Srivastava, and Akash Sanghi.

## Study contents

- `acr_mcr_v2.py` — transaction-level simulator, forecaster, calibrator, and controller.
- `PROTOCOL.md` — computational protocol and prespecified comparisons.
- `MODEL.md` — model assumptions and metric definitions.
- `run_study.py` — complete 1,280-run outcome experiment.
- `results/raw_results.csv` and `results/raw_results.jsonl` — all 1,280 outcome runs.
- `results/rounds/` — per-round records for all 1,280 runs.
- `results/links/` — transaction-level diagnostic records for the designated primary diagnostic seed.
- `results/manifest.json` — execution environment, source SHA-256 hashes, and complete job configurations.
- `test_mechanisms.py`, `verification.json` — thirteen executed mechanism checks.
- `analyze_study.py`, `analysis/` — paired analyses, multiplicity correction, coverage diagnostics, sensitivity summaries, and timing profiles.
- `profile_study.py` — thirty separate serial host-timing runs.
- `plot_figures.py`, `diagram_figures.py`, `figure_text.py`, `figures/` — deterministic figure sources and rendered figures.
- `release_validation.json` — release-level consistency checks.
- `checksums.sha256` — integrity hashes for the archived scientific release.

## Experimental scope

The primary study uses 30 matched seed blocks, five dynamic regimes, and seven controller variants (1,050 primary runs). Stationary-control, scalability, probe-budget, and fixed-head-count experiments add 230 runs, yielding 1,280 outcome runs in total. Thirty timing runs are separate from outcome inference.

The study is simulation-based. It does not contain measured radio traces, a physical deployment, or ns-3 packet-level validation. The randomized control is `RANDOM-CH`; it is not presented as LEACH.

## Reproduce the saved analyses

The archived execution environment used Python 3.12.14, NumPy 2.3.5, pandas 2.2.3, SciPy 1.17.0, and Matplotlib 3.10.8.

```bash
python -m pip install -r requirements.txt
python analyze_study.py
python plot_figures.py
```

The analysis verifies the locked simulator and protocol hashes before recomputing derived tables. Numeric CSV results should reproduce within floating-point tolerance; gzip timestamps and image metadata may differ after regeneration.

## Fresh replay

Use a separate directory rather than overwriting the archived evidence:

```bash
mkdir replay
cp acr_mcr_v2.py test_mechanisms.py run_study.py analyze_study.py profile_study.py plot_figures.py diagram_figures.py figure_text.py PROTOCOL.md replay/
cd replay
python test_mechanisms.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python run_study.py
python analyze_study.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python profile_study.py
python plot_figures.py
```

For a single diagnostic run:

```bash
python acr_mcr_v2.py --method ACR-MCR --scenario S5 --seed 9000
```

Seed 9000 is a debugging seed and is not part of the reported inference.

## Statistical interpretation

Scenario values are averaged within each seed before the primary paired comparison. The 168,000 primary round records are dependent repeated records and are not treated as independent trials. `analysis/primary_effects.csv` reports ACR-MCR minus POINT-EA. The Holm correction for the co-primary analysis covers timely delivery and service-violation rate. Other scenario-specific and sensitivity intervals are exploratory and pointwise.

## Integrity

`results/manifest.json`, `verification.json`, `analysis/analysis_verification.json`, `release_validation.json`, and `checksums.sha256` provide the principal reproducibility and integrity records for this release.
