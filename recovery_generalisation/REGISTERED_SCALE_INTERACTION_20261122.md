# Independent confirmation of the network-size interaction

Date registered: 22 November 2026, after **exploratory discovery**
in the completed 360-run cohort using seeds 9701-9710, but BEFORE
the 9901-9910 confirmation outcomes are collected. This is not a
claim of wholly a priori discovery. Preserve both cohorts separately.

Scientific question: Does the ACR-MCR minus POINT-EA service effect
change systematically between 40-node and 120-node networks, under
identical per-node probe budgets, original optimizer settings and
six original environmental regimes?

New independent topology seeds: 9901-9910, none reused from discovery.
Network sizes: 40,120. Regimes: S0,S1,S2,S3,S4,S5.
Policies: POINT-EA,ACR-MCR, original unmodified source.
Rounds: 160, first 20 warmup excluded as in the original study.
Probe allowance: one per source per round, policy-independent schedule.
Total: 10 seeds x 2 sizes x 6 regimes x 2 policies = 240 runs.

For each seed and scenario, compute the ACR-minus-POINT signed
difference at N=40 and N=120, then the N=120 minus N=40
**interaction of the policy effect**. Average the six scenario
interactions within each seed to yield ten independent values.

Co-primary interaction estimands:
1. Timely-delivery difference-in-differences.
2. Service-violation-rate difference-in-differences.
Report two-sided paired-t 95% CIs, p-values and two-step Holm adjusted
p-values, including all unfavourable results. The source 360-run cohort
is discovery only and must not be pooled with confirmation to claim
independence. Energy/probe control, search counts, and route changes
are exploratory correlates, not proof of causation.

A significant scale interaction would be a bounded new **negative
decision-value finding** within the mathematical simulator. It does
not establish that the *algorithmic integration* is original in the
literature or generalises to PHY/hardware. That requires verified
comparative citations and full closed-loop physical validation.
