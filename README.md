# ACR-MCR Dynamic IoT-WSN — Data and Reproducibility

This repository contains the code, data and reproducibility material supporting the manuscript:

**Adaptive Conformal Clustering and Routing In Dynamic IoT Sensor Networks Under Explicit Telemetry Costs**

Authors: Shivam Bhardwaj, Jitendra Nath Srivastava, and Akash Sanghi.

## Study snapshot

The archived study is a transaction-level synthetic IoT/WSN experiment. It contains:

- 1,280 outcome runs in total.
- 1,050 primary runs: 7 controller variants × 5 dynamic regimes × 30 paired seeds.
- 1,280 compressed per-round output files.
- 35 transaction-level diagnostic-link files for the primary seed-1000 runs.
- 30 separate timing-profile runs.
- 13 executed mechanism/consistency checks.
- Saved statistical analyses and deterministic figure-generation sources.

The primary controllers are RANDOM-CH, POINT-EA, FROZEN-CP, ROLL-CP, ACI-PER, ACI-EVENT, and ACR-MCR.

## Repository structure

- `acr_mcr_v2.py` — simulator, observable forecaster, calibrator and controller.
- `PROTOCOL.md` — locked computational protocol.
- `MODEL.md` — model assumptions and metric definitions.
- `test_mechanisms.py` and `verification.json` — mechanism checks.
- `run_study.py` — 1,280-run study runner.
- `results/raw_results.csv` — all per-run outcomes.
- `results/rounds/` — compressed per-round outputs for all outcome runs.
- `results/links/` — issued-bound and observation diagnostics for seed 1000.
- `analyze_study.py` and `analysis/` — paired statistics, multiplicity control and coverage diagnostics.
- `profile_study.py` and `analysis/timing_profile.csv` — separate timing experiment.
- `plot_figures.py`, `diagram_figures.py`, and `figures/` — deterministic figures.

## Primary design

The primary experiment uses 40 sensors, 160 rounds, a 20-round warm-up, seeds 1000–1029, five dynamic regimes (S1–S5), and seven matched controller variants. Scenario outcomes are averaged within each seed before paired inference. The 168,000 primary round records are repeated observations within runs and are not treated as independent statistical units.

The co-primary comparison is ACR-MCR minus POINT-EA for timely delivery and service-violation rate. The saved analysis reports paired mean differences, 95% Student-t intervals, two-sided sign-flip Monte Carlo p-values and Holm correction over the two co-primary outcomes.

## Reproduce the saved analysis

Create an isolated Python environment and install:

```bash
python -m pip install -r requirements.txt
python analyze_study.py
python plot_figures.py
```

A fresh replay can be executed in a separate directory with:

```bash
python test_mechanisms.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python run_study.py
python analyze_study.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python profile_study.py
python plot_figures.py
```

Timing results depend on the host and are not expected to be byte-identical across machines. The reported scientific claims are limited to the declared synthetic network model; this repository does not claim physical-hardware or packet-level ns-3 validation.

## Data availability

All study data and reproducibility material associated with this repository are publicly accessible here. The repository intentionally excludes manuscript drafts, reviewer/editor correspondence and submission-packaging files so that the public record remains a scientific reproducibility resource.
