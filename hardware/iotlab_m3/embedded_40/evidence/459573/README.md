# Real Grenoble M3 deterministic original-controller kernel experiment 459573

Method: POINT-EA. Real physical board: M3-14.
Original Python synthetic fixture: POINT-EA_9401_S1_r20.
Real hardware C plan fitness+search: PASS, heads [4, 7, 9, 23];
M3 score differs by 18 nanounits.
Controller wall 0.15 s.
This is an M3 *decision kernel*, not a deployed original adaptive
40-node end-to-end controller. The original NumPy RNG draws and synthetic
network state were frozen in Flash to provide a controlled parity check.

Raw external control-node device current/voltage/power OML is included,
but the first run's duration/samples failed a preexisting >=25-sample,
>=40s power quality gate; no physically validated session Joules or
per-decision Joules are asserted from this short file. No Apple M1
host power samples exist here.

Source SHA256 and original raw UART log are saved for independent
audit. Do not infer a statistical physical service advantage or
calibrated SNR-to-PER relation from this one-fixture program test.
