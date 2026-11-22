# Preregistered on-M3 original decision kernel and real radio baseline

Frozen BEFORE physical data, 22 November 2026.

Physical design: 40 deployed M3 source nodes plus an M3 sink using
the source-hashed Grenoble V2 layout of experiment 459568.
The ORIGINAL Python-equivalent deterministic ACR-MCR or POINT-EA
C make_plan, fitness, CVaR and 8x4-generation survivor-search
kernel runs on the real M3 sink at boot. The sink then emits the
selected full plan over two real radio control segments to the
40 M3 sources. Sources relay one exactly 500-byte sample in eight
fragments per 20-second round (3 rounds per trial), with the same
nominal denominator 120 source-rounds per baseline. Reassembled
500-byte sink samples must pass content-level verification.

Controlled input: original simulator source SHA
3f134a8826525215f7cf2ff307bab3893c0d64b050f742bdc3c250b1c0302ea4.
Hold seed9401, scenario S5, original round20, and exact candidate/
stress index NumPy RNG draws frozen in firmware FLASH. ACR-MCR's
conformal/CVaR program and POINT-EA use their matching original
method-specific synthetic prediction/fitness matrices; do NOT
substitute physical environment measurements or modify original
algorithms. Preselected expected original heads are independently
checked against actual on-mote chosen head IDs.

Both methods run on SAME physical 41-node layout, independent physical
reservations of a single 3-round block each. Record actual
firmware, original UART for all 41 devices, sink-selected heads,
absolute Python/C objective discrepancies, actual control installs,
source demand, MAC callbacks, 500-byte sink integrity, and ENERGEST.
Every failed and unobserved packet remains in the original
40*3=120 demand denominator, not a software failure.

Limitations: This is an OPEN-LOOP physical comparison.
The member nodes' physical MAC outcomes DO NOT update the frozen
synthetic model, conformal calibration, next heads or risk optimizer;
no NumPy RNG runs natively on-M3, original multi-round state evolution
is not implemented. Frozen coordinates and path costs were generated
for the synthetic simulator, NOT measured at Grenoble.
One 3-round physical block per method supplies NO independent-seed
confidence intervals or p-values and is NOT validated superiority.
Do not report source-to-sink 500ms physical deadlines from UART
without synchronized clocks. Apple host power in J is NOT measured.
Full 40-node physical closed-loop adaptive algorithm remains
[NEED SOURCE].
