# Actual AC wall-plug electricity measurement: prepared, not performed

On 22 November 2026 the Mac showed a 15 W rated charger, 78% charging battery,
no UPS, zero USB devices and no accessible smart power-meter app or local
meter service. Rating is not actual instantaneous mains power. Real calibrated
AC Joules CANNOT be inferred from the Apple CPU-power trace.

Physical prerequisite: connect an AC true-real-power energy meter or power
analyzer between wall socket and ONLY the Mac charger, with timestamped real
power readings in watts and independently checkable calibration evidence.
The current battery is charging; for reproducible incremental CPU comparisons,
stabilize battery charge (prefer fully charged), keep brightness/temperature
and other laptop loads steady, and record battery state in the experiment log.
Do not modify electrical wiring or safety protections.

Original simulator SHA256:
3f134a8826525215f7cf2ff307bab3893c0d64b050f742bdc3c250b1c0302ea4.
Frozen test protocol: IDLE, POINT-EA, ACR-MCR, ACR-MCR, POINT-EA, IDLE.
Each method phase uses 100 original full-model simulations: five complete
repeats of two scenarios S1/S5 and ten seeds 10301..10310, 40 nodes,
160 rounds. Original power_batch_worker.py is unchanged. Repeat entire
six-phase sequences on independently scheduled blocks to estimate uncertainty.

Record all true AC power data in meter_power.csv with fields
timestamp_utc,power_W, sample period no more than 3 seconds, timestamps
synchronized to the Mac. Record 6 immutable start/end instants in
phase_boundaries.json. Record wattmeter model, serial, declared accuracy,
calibration document original SHA256, and clock evidence in
meter_identity.json. The wattmeter's calibration must be independently
verified; file presence alone does not certify calibration.
Integrate real-power time series in joules by trapezoids. Baseline-
adjusted incremental input electricity still includes charger losses,
battery-current changes and whole Mac activity; it is not optimizer-only
energy. Two runs per method cannot support a reliable inferential CI.

No measured wall-plug watts/Joules currently exist. Do not write numeric
values into the paper before obtaining real external instrument data.
