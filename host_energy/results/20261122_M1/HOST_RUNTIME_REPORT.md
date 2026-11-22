# Apple M1 matched ACR-MCR host computation benchmark

22 November 2026; original unmodified simulator, 40 source nodes, 160 rounds.
Ten independent matched seeds 10301..10310, scenarios S1/S5, two policies,
40 source-locked process-isolated outcomes; order balanced by seed.

| Measured time (mean per run) | POINT-EA | ACR-MCR |
|---|---:|---:|
| Controller select() wall seconds | 0.118231 | 0.177393 |
| Process CPU seconds | 0.451839 | 0.517740 |
| Total process wall seconds | 0.458703 | 0.522494 |
| Fitness evaluations | 534.95 | 550.95 |

ACR-MCR's measured controller wall time was 50.04% longer.
The original model also simulates network traffic, so process CPU
time is not exclusively the optimizer. Results describe one Apple M1 Mac.

No physical host Joules were measured. Apple powermetrics needs root
access and the authorized remote command service does not allow sudo.
AC battery current is not a CPU-package energy measurement.
Do not multiply processor time by invented watts.
Power measurement requires an authorized system power instrument
or calibrated external meter with synchronized idle baseline.

Original simulator SHA256: 3f134a8826525215f7cf2ff307bab3893c0d64b050f742bdc3c250b1c0302ea4

All 40 raw records retained in JSONL and CSV with a SHA256 manifest.
