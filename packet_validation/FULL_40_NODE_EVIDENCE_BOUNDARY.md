# Full-size (40-node) Cooja evidence: explicit scope and acceptance gates

**Do not confuse the presence of 40 sensors with full closed-loop ACR-MCR validation.**

## Implemented and verified
- The **unmodified original Python controller** (acr_mcr_v2.py, source SHA
  recorded in exported provenance) still runs the original 8-candidate,
  4-generation cluster-head search, path assignment, adaptive calibration,
  and empirical tail-risk objective, exactly as in the submitted code.
- For each fresh seed and regime, its 40-node per-round assignments,
  backbone next hops and policy-independent one-probe schedule are exported.
- The route, node positions and probe target enter a 41-mote Contiki-NG/Cooja
  scenario (40 sensors + one sink).
- Cooja executes actual CSMA packet transmissions and acknowledges/fails
  unicast attempts. Motes perform member-to-head, head-to-next-hop and
  sink delivery, with MAC retry callback logs.
- The ScriptRunner captures source demand, unique source/round sink receipts,
  attempt counts and global-simulation-time end-to-end latency.
- S5 applies the original model's node-disable flags to the simulated
  Contiki radio; its Cooja receive-success probability is fixed at 0.82
  (S1: 0.94), not a reimplementation of all original interference dynamics.
- A frozen local 16-round POINT-EA S1 feasibility run for seed 8101 passed:
  40 sensor nodes, 640 samples queued, 640 unique sink receptions,
  1,938 MAC callbacks, zero failed MAC callbacks. This is a smoke test.
- GitHub Actions provides a 160-round by 40-sensor matrix across two fresh
  seeds, two regimes and two matched controller policies.
  Run URL: https://github.com/DrShivamBhardwaj/ACR-MCR_Dynamic_IoT_WSN_Data/actions/runs/44993865721

## What this experiment is NOT
The per-round head/path choices are updated using **synthetic observations
inside the original Python simulator**, NOT Cooja ACKs or Cooja service
misses. This is an OPEN-LOOP policy replay. The experiment can expose
packet-level feasibility problems and sensitivity to MAC contention, but
cannot establish the performance of a fully packet-driven ACR-MCR controller.

Cooja currently carries a short 78-byte packet, not the original 4,000-bit
payload. The 500-byte payload requires fragmentation/reassembly over
IEEE 802.15.4 data frames. There is no implemented distributed telemetry
collection and no actual two-broadcast-per-sensor per-search control exchange;
those were debited only by the original abstract model. CPU, idle listening,
sensor consumption and physical radio energy remain unmeasured. The Cooja
UDGM radio settings are simulation parameters, not external PER calibration.
Only POINT-EA and ACR-MCR are replayed, not all seven controller variants.

The replay currently sends one source sample per node and round,
not each original model's possibly changing offered-load multiplicity.
This discrepancy must be corrected in a full transport-port assessment.

## Scientific acceptance checklist for *full* original-controller validation
- [ ] Ingest real packet-level ACK, retry, latency and queue observations
      into the **next controller round**; never use abstract environment
      observations to adapt the policy when making full-port claims.
- [ ] Reproduce original 40-node traffic loads and dynamic interference,
      all five changing regimes, feasible range and node failure schedule.
- [ ] Fragment and reassemble the original 4,000-bit payloads and implement
      the original member-to-head aggregation and backbone packet flow.
- [ ] Replace ideal controller status broadcasts with actual communication,
      including route collection, measurement and dissemination overhead.
- [ ] Validate event timing, pre-update calibration, objective coefficients,
      64 tail-risk draws, four generations and accepted-head changes using
      keyed reference traces from the original Python code.
- [ ] Execute fresh independent seeds against matched POINT-EA on registered
      estimands, correcting multiple inference tests.
- [ ] Quantify CPU/memory energy on a supported target. External SNR/PER
      calibration and physical measurements are needed for hardware claims.

**Status:** partial independent packet-transport validation, not scientific
closure of Discover Networks Reviewer 1. All unresolved requirements are
explicit; no synthetic/packet data are interchanged.
