# Statistical analysis note

The primary inferential unit is the matched topology/environment seed. For each method and seed, the five dynamic regimes S1-S5 are averaged first, producing n=20 independent seed-level values per method for the primary comparison.

Two outcomes were designated as co-primary in the manuscript:

1. packet delivery ratio (PDR), and
2. operational risk-violation rate.

The prespecified primary comparison is ACR-MCR versus POINT-EA on the ALL_DYNAMIC seed-level aggregate. Two-sided Wilcoxon signed-rank tests are used for hypothesis testing, paired mean differences are accompanied by two-sided 95% t confidence intervals, and paired Cohen dz is reported as an effect-size descriptor.

Holm multiplicity correction is applied only across the two co-primary tests above. The resulting adjusted p-values are:

- PDR: raw p = 0.009436; Holm-adjusted p = 0.018871.
- Operational risk-violation rate: raw p = 0.044187; Holm-adjusted p = 0.044187.

All scenario-specific tests, secondary-outcome tests, and comparisons against other conformal variants are exploratory. The output file `paired_stats_20seed.csv` therefore contains two separate multiplicity columns:

- `primary_holm_p`: populated only for the two prespecified co-primary tests.
- `exploratory_holm_across_scenarios`: an auxiliary correction across the six scenario scopes within each comparator/metric family; this column is not used for the manuscript's primary claims.

This separation prevents an exploratory multiplicity family from being confused with the prespecified primary analysis.
