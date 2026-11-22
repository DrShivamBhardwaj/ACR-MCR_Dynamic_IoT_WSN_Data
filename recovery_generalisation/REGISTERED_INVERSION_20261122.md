# Independent confirmation of reliability–deadline inversion

**Registered on 22 November 2026, after discovering the candidate pattern
in the 360-run original-simulator cohort, but before this new cohort.**

Question: At 120 nodes, under a fixed per-node telemetry budget, does
ACR-MCR increase eventual packet-delivery probability while reducing
delivery by the 500ms deadline, relative to the identical POINT-EA
optimizer using point estimates?

- Original simulator source acr_mcr_v2.py is unchanged.
- Independent seeds: 9951–9960, not previously used in any cohort.
- N=120, regimes S0,S1,S2,S3,S4,S5, 160 rounds, 20 warmup.
- Matched POINT-EA and ACR-MCR, probes=1, same random-key fields.
- 10 seeds x 6 regimes x 2 methods = 120 registered runs.
- Independent unit: seed. For each seed average the six scenario
  effects (ACR-MCR minus POINT-EA).
- Co-primary H1: PDR difference; H2: timely-delivery difference.
  Two-sided paired-t p-values, 95% Student-t CI, and Holm across H1/H2.
- A reliability–deadline inversion requires PDR effect > 0 and timely
  difference < 0, **both Holm-adjusted p < 0.05**. If either fails,
  do not claim confirmed inversion.
- Service violation, radio/probe energy, search counts, and head changes
  are exploratory. Do not assert mechanism causation without targeted
  interventions on head selection, packet queues and telemetry.
- No reseeding, dropping adverse regimes, or adding retrospective tests
  to the confirmatory family.

The independently repeated result, if obtained, is a bounded effect
inside the SAME original synthetic transaction model. It cannot be
portrayed as Cooja/PHY/hardware confirmation or proof of originality
relative to all literature. Manuscript revisions must preserve this
source/model boundary.
