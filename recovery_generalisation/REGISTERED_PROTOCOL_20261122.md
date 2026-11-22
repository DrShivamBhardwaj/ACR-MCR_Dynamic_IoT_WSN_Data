# Independent scope test of the frozen ACR-MCR controller

**Protocol frozen before fresh generalisation runs.**
Study: Discover Networks rejection recovery, 22 November 2026.
This analysis is separate from original released 1,280 runs and from the
packet-feedback Cooja co-simulation.

## Main question and evidence
The original ACR-MCR did not establish co-primary service superiority over
POINT-EA. This independent study asks whether that conclusion changes
materially with topology size and environmental regime. No revised method
is introduced, trained or selected using the confirmation seeds.

## Registered matrix
- Original source: acr_mcr_v2.py, unchanged.
- Seeds: 9701–9710, ten independent topology/traffic blocks.
- Size: N = 40, 80, 120.
- Scenario: S0 (stationary) and S1, S2, S3, S4, S5 as defined by the
  original model. No scenario is removed if it performs badly.
- Controllers: ACR-MCR and POINT-EA, equal configurations and random-field keys.
- 160 rounds per configuration, initial 20 rounds warm-up.
- Probes: one per source per round, same route-independent schedule.
- 6 scenarios x 3 sizes x 10 seeds x 2 methods = **360 outcome runs**.
- Registered primary endpoints: timely delivery and service-violation
  rate, both expressed as ACR-MCR minus POINT-EA. Report PDR, modelled
  radio energy, probing energy and cost per delivered sample descriptively.

## Analysis and multiplicity
For each independent seed, average its 18 scenario x size paired effects,
then report mean across the ten independent seeds, two-sided 95% Student-t
confidence intervals, and paired t-test p-values. Adjust the two primary
p-values using Holm. Scenario/size plots are exploratory descriptions
with no subgroup significance or superiority claims. No replacement seeds
or post-hoc protocol tuning based on confirmation results. Fail the entire
audit if any registered cell is missing, duplicated, NaN in the primary
estimands, or lacks source provenance.

## Limits
This is generalisation **within the original synthetic model**, not external
or physical validity. It cannot substitute for Cooja packet-feedback,
embedded CPU/radio energy, calibrated RF channels, 500-byte payload
fragmentation, or distributed controller telemetry.
A null or negative result is a legitimate finding and must be retained.
