# New native over-radio source telemetry prototype, registered before testbed

Source derived from previously physically tested static cluster transport,
without editing original ACR-MCR Python or previously frozen M3 binaries.

Physical M3 roles: logical 1/2 sources, logical 41 sink, three
rounds. After each source transmits a real MAC probe, it logs native
transmit-service ticks and the driver success/attempt result.
It queues an eight-byte observation frame, type5, to its
radio-installed route, preserving source/destination/round,
attempts, success, duration_ms, driver status and type provenance.
Intermediate cluster head forwards the frame over actual physical
radio. Sink logs a unique SINK_REAL_PROBE_OBS for each source-round.
UART hardware acknowledgements are NOT spoofed or read centrally.

Acceptance: fresh reservation, 3/3 firmware flashes, all three
original UART streams and firmware hashes, at least one actual
PROBE_TX_EVIDENCE and matching SINK_REAL_PROBE_OBS. All missing
telemetry is an outcome. Missing round/ACK evidence does not
authorize a fabricated sample. Retain failures and full original logs.

This STAGE IS NOT ORIGINAL ADAPTIVE ACR-MCR. Original per-link
Bayesian predictor, residual score/coverage update, conformal
calibrator integration, candidate RNG, risk/CVaR search, next-round
plan update and deadline comparisons are NOT implemented here.
A source-local MAC TX clock is not a cross-node time-synchronised
500ms application deadline. The plan remains the STATIC four-head
map and remains experimentally distinct from frozen C risk kernel.
