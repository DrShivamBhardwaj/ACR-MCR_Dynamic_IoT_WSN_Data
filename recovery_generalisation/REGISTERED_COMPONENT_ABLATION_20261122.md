# Independent 120-node mechanistic component ablation

Protocol frozen 22 November 2026 after an exploratory 360-run cohort
suggested delivery/deadline trade-off. This fresh experiment separates
existing components of the ORIGINAL ACR-MCR simulator. It does not
alter the frozen 1,280-run release or invent a new method.

Seed blocks: 9971–9980 (unused in earlier cohorts).
Regimes: S0,S1,S2,S3,S4,S5.
Nodes: 120; rounds:160; warmup20; probes=1 each source per round.
Four ORIGINAL controllers:
  POINT-EA: point estimates, no event trigger, no tail regularizer
  ACI-PER: adaptive conformal bounds, periodic search, no tail term
  ACI-EVENT: adaptive conformal bounds + event-driven search, no tail
  ACR-MCR: adaptive bounds + event search + empirical tail regularizer
Total 10 seeds x 6 regimes x 4 methods = 240 runs.

Registered primary comparisons on timely-delivery ratio:
 (1) ACI-PER minus POINT-EA (bound substitution),
 (2) ACI-EVENT minus ACI-PER (event scheduling increment),
 (3) ACR-MCR minus ACI-EVENT (CVaR tail-penalty increment).
Use scenario-average per independent seed (n=10) and two-sided
paired-t 95% intervals and p-values with Holm across three tests.
Report adverse/null outcomes. PDR, search counts, head changes,
controller CPU time, radio/probe energy and service violation remain
exploratory; these are not externally calibrated energy measurements.

Component differences are controlled within the existing code but
remain affected by the adaptive trajectories and control-path context;
a marginal difference is not automatically a general causal law in
wireless networks. All six regimes and ten seeds must complete.
No claim of scientific novelty before literature comparison.
