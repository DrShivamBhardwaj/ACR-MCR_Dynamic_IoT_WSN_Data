# Native Grenoble M3 three-node transport smoke, experiment 459566

Grenoble physical M3-14 source1/head, M3-15 source2 and M3-18 sink logical 41. Three 20-second rounds with sink-generated FIXED four-head route plan (not adaptive ACR-MCR). Two real radio-control segments per round, and 500-byte application samples split into eight MAC fragments.

Strict trace audit PASS: 6/6 planned source-round samples fully reassembled and byte checked at sink; both sources applied all three rounds of radio-delivered control, and 24/24 forwarded source2 fragments passed via source1 to sink. All 3 ENERGEST logs collected. This is a two-source multihop transport-only smoke. It does not demonstrate 40 physical sensor nodes or the original Python optimizer running on embedded hardware. Cross-node 500ms latency cannot be inferred from unsynchronised UART clocks.
