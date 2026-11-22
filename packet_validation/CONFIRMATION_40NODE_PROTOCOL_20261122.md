# Prespecified independent-seed 40-node packet-transport confirmation

Registration date: 22 November 2026. This document is committed before
executing the NEW confirmation seed blocks 8201 through 8210. The earlier
seeds 8101 and 8102 are excluded from inferential analysis.

## Exact research scope
This is confirmation of **40-node open-loop route-replay feasibility under
Cooja packet access**. It is NOT a confirmation of fully packet-driven
ACR-MCR adaptation or a field-deployed network. The original optimizer
(8 candidates, 4 generations, tail-risk term, calibration) runs in Python,
and exports a precomputed route/control schedule for each seed/variant.
**Synthetic** Python observations determine subsequent routing decisions.
Cooja supplies new MAC and sink outcomes but does not update the optimizer.

## Locked matrix
- Sensor nodes: 40 plus one sink, with original source-generated positions.
- Rounds: 160 each, no truncation of simulation data.
- Fresh independent synthetic-topology and Cooja seed blocks:
  8201, 8202, 8203, 8204, 8205, 8206, 8207, 8208, 8209, 8210.
- Regimes: S1 (nominal fixed Cooja radio success 0.94); S5
  (original model's failed-node schedule with Cooja success 0.82).
  The full time-varying Python interference law is NOT reproduced by Cooja.
- Paired methods: POINT-EA and ACR-MCR, identical seed and radio settings.
- One short data source frame per node per round and one route-independent
  probe per source per round, where assigned and active. Original Python
  model expects a 4,000-bit payload and possibly two samples/round.
- Full outcome denominator: **40 x 160 = 6,400** source-round demands per
  scenario and method. Unassigned or disabled sources count as missed.
- All data files include provenance hash, original source hash, schedule
  hash, Cooja testlog, retransmission status and explicit limitations.

## Co-primary estimates and analysis rule
For each fresh seed, calculate (ACR-MCR minus POINT-EA) separately in S1
and S5 for:
1. Unique sink delivery / 6,400 fixed source-round demands.
2. Unique sink receipts within 500ms of globally timestamped source
   queueing / 6,400 fixed source-round demands.

Average the S1 and S5 effects **within each seed**. The 10 seed means
are the independent units. Use 2-sided paired t-tests against zero and
95% t-based CIs; apply Holm's step-down correction across the two
co-primary p-values. Report raw effects, CI, and adjusted p-values even
when they are zero or unfavourable. No post hoc subset selection will be
used to claim superiority. Scenario-specific and energy-proxy metrics
remain exploratory. CPU and total radio energy are not estimated from
the Cooja attempt logs. If any of the 40 registered scenario/method/seed
runs is incomplete, do NOT declare confirmation complete and exclude
the entire incomplete seed only with explicit justification; do not
substitute new seeds after inspecting outcomes.

## What success can and cannot show
PASS means all runs completed with trace/provenance consistency and
proper statistical reporting, not that ACR-MCR outperformed POINT-EA.
Because the controller decisions come from the frozen abstract source,
this experiment provides independent packet-level communication
stress evidence rather than original-controller closed-loop scientific
validation. Original payload fragmentation, distributed telemetry,
full dynamic interference, idle/CPU energy and hardware calibration
remain separate requirements.
