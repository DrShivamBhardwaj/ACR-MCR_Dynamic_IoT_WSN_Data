# Root-authorized Apple M1 CPU-subsystem power: independent raw-interval audit

The owner-approved six-phase sample was independently checked against original
powermetrics CPU power, sample elapsed milliseconds, source SHA256 and complete
100-case workload files. Every stage met the registered order and trace-density
requirements. These are **Apple-estimated CPU subsystem energies**, not
independent calibrated electrical-energy measurements.

| Method | 100-case phase 1 (estimated baseline-adjusted J) | Phase 2 (J) | Mean per full simulator case (J) |
|---|---:|---:|---:|
| POINT-EA | 173.099 | 224.104 | 1.9860 |
| ACR-MCR | 252.160 | 201.853 | 2.2701 |

Exploratory ACR-MCR minus POINT-EA difference: +0.2840 estimated CPU-subsystem J per full simulator case.
This is *not* optimizer-exclusive energy, because each workload executes the
complete Python simulator and all other Mac processes affect aggregate power.
Both methods were measured only twice, in a nonrandomized order. Neither
a calibrated physical electrical-energy measurement nor an inferential
energy advantage/disadvantage can be established from these two blocks.

Original immutable model SHA256: \`3f134a8826525215f7cf2ff307bab3893c0d64b050f742bdc3c250b1c0302ea4\`.
The full six original unedited powermetrics traces, workload records and
interval-level time verification are preserved with SHA256 manifest.
Sampling was conducted with local root authorization rather than a
Remote Desktop Commander privilege escalation. No more administrator
permission is needed to preserve, inspect or recompute existing evidence.
