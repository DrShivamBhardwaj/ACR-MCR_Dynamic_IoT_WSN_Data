# Original M1 Apple estimated package-power capture, authorization gate

Prepared 22 Nov 2026, source SHA256
3f134a8826525215f7cf2ff307bab3893c0d64b050f742bdc3c250b1c0302ea4.

The installed system powermetrics CPU power sampler MUST be operated
with local macOS administrator permission. This chat's authorized
Remote Desktop Commander is deliberately blocked from privilege
escalation. No privileged action was taken from the chat.
The collector collect_m1_power_authorized.py enforces
os.geteuid()==0 and will not claim measurement without it.
The local account owner needs to authorize its execution in their
own Mac Terminal later; credentials must never be shared in ChatGPT.

Frozen protocol once authorized: same M1 device, original Python
simulation, 40 nodes, 160 rounds, same 10 seeds 10301-10310,
S1/S5, 5 repeated complete 20-case blocks per method.
Order: IDLE / POINT-EA / ACR-MCR / ACR-MCR / POINT-EA / IDLE.
Each independently captured phase uses installed Apple
powermetrics CPU-power sampling at 1s intervals and frozen
original code, collecting raw traces and long enough matched
CPU workloads. Aborted phases remain recorded. Do not omit or
change unfavorable observations.

Instrument scope: Apple powermetrics reports estimated
CPU subsystem power, not calibrated wall-plug electricity,
not exclusively the Python process, not M3 board power.
Actual calibrated host electrical Joules additionally require
an external power meter or reliable instrument calibration.
Estimated power integration, if performed, must subtract
appropriate idle baselines with uncertainty and be labeled
Apple-estimated subsystem energy, not experimentally calibrated
Joules. No physical host energy figure has yet been obtained.
