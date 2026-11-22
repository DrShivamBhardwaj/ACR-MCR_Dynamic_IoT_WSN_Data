# ACR-MCR rejection recovery: evidence-first computation plan
Status: implementing pipeline, not a revised manuscript or acceptance guarantee.
Decision record: Discover Networks, 22 November 2026, submission 7f93f439-f959-4371-a478-e1062ea986dc.

## Ground truth and protection
The previous 1,280-run protocol, results and scripts are retained unchanged.
The baseline state is Git SHA 7dceb22340677ee78a9f36c8dd4c96ad5988509c.
The old private repository contains a DIFFERENT legacy code/study and is not interchangeable
with acr_mcr_v2.py, which generated the released transaction-level study.

Release-level co-primary contrasts (ACR-MCR minus POINT-EA, 30 paired seed blocks):
- Timely delivery difference -0.0021298124, 95% CI [-0.01065528, 0.00639566], Holm p 0.61550.
- Service violation difference -0.0073333333, 95% CI [-0.01840533, 0.00373866], Holm p 0.37934.
Neither co-primary contrast establishes an improvement.
Saved data imply probes consume about 49.84% of ACR-MCR modelled radio energy.
The simulator omits controller CPU energy, idle listening and a fully distributed telemetry protocol.

## GitHub Actions as the primary executor
Repository: DrShivamBhardwaj/ACR-MCR_Dynamic_IoT_WSN_Data (PUBLIC).
Standard GitHub-hosted runners in public repositories do not count against the
private repository minutes allowance. Avoid larger/paid runners.
Never publish unpublished manuscript text or private credentials into this public repo.

1. ACR-MCR Scientific Audit:
   - scheduled daily at 03:19 UTC on the default branch, and on relevant pushes;
   - verifies locked source/protocol hashes, 1,280 manifest matches, the 30 paired
     seed blocks, the exact two co-primary outcomes and diagnostic energy fractions;
   - executes existing 13 mechanism tests, reruns released statistical analyses;
   - saves short-lived reports as Actions artifacts; never commits generated raw results.
2. ACR-MCR Fresh Paired Pilot:
   - triggered manually via Actions workflow_dispatch;
   - preflight runs tests/audit before any new simulation;
   - runs all five dynamic regimes across two non-overlapping pilot seed blocks,
     ACR-MCR and POINT-EA, parallelized up to four standard Linux runners;
   - 1 to 5 seeds per block, uses seeds 9100 onward exclusively for exploratory checks;
   - writes run-specific CSVs, provenance JSON and an aggregate mean-difference diagnostic;
   - no hypothesis testing, no claims of novelty or statistically significant benefit.
   - accepts no baseline comparison changes or retrospective tuning.

## Reviewer issue -> evidence gate
R1: Introduction has no citations -> build a verified source ledger. [NEED SOURCE]
R1: Weak critical synthesis -> method-by-method gap table against relevant literature. [NEED SOURCE]
R1: Unclear novelty -> isolate value of uncertainty-aware decisions beyond matched point
    decisions at equal search budget, objective weights, probes and control accounting.
R1: Primary superiority not established -> retain negative effect estimates and CIs.
    If a new policy is designed, freeze a revised protocol BEFORE independent confirmation.
R1: Synthetic assumptions -> test scheduling, ACK, interference and telemetry mechanisms
    with packet-level Cooja/Contiki-NG scenarios; compare with existing model assumptions.
    Cooja alone is not physical validation. Avoid describing a standalone RPL smoke test
    as validation of ACR-MCR unless the ACR-MCR decisions are actually implemented.
R1: Generalizability -> independent seeds, topology/traffic sensitivity, explicitly
    labelled exploratory and confirmatory analyses, with no cherry-picked endpoints.

## Cooja implementation acceptance criteria
Phase C0: Cooja/Contiki-NG can build and execute an existing packet-level regression.
Phase C1: retain packet TX, ACK, retransmissions, latency and contention traces.
Phase C2: define identical decisions and telemetry collection for ACR-MCR and point control,
          port or replay their decisions at MAC-accessible times (not just route labels).
Phase C3: compare radio/telemetry accounting and service outcomes across independent seeds.
Status of C1-C3: NOT VERIFIED. No full port or physical evidence is claimed.

## Cost and privacy safeguards
- GitHub standard ubuntu-latest only, not paid larger runners.
- Artifact retention 7 days (audit), 10/14 days (pilot); do not push bulk logs.
- Paired pilots have bounded inputs and hard job timeouts.
- Main branch protections: no auto-edit to frozen 1,280-run release, no result rewrite.
- Python package versions match the archived environment.
- For Cooja, the Mac is an optional secondary build environment only; keep large
  computational runs on Actions and reserve Mac use for hardware-specific checks.
- GitHub's scheduled workflows require presence on the default branch and may stop
  after prolonged inactivity; inspect Actions if a run is not delivered.
