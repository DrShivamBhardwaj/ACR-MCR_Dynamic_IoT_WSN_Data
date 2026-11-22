# Remaining host electrical-energy calibration gate

Device: Apple M1 MacBook Air (8GB), macOS. Original paired benchmark
finished 22 November 2026 and is archived under results/20261122_M1.
This instrumented the controller's Python select() wall time, process
user/system CPU time, and simulator time for 40 independent matched
policy/scenario/seed cases. Results cannot be converted into Joules.

The installed /usr/bin/powermetrics reports that superuser access is
required. The authorized Remote Desktop Commander interface blocks
sudo, so this ChatGPT session did not elevate privileges, disable
system authorization, or fabricate CPU power. Apple itself describes
powermetrics CPU power as ESTIMATED subsystem power, potentially inaccurate.

A future measurement requiring explicit local administrator approval
may sample package CPU power across matched idle, POINT-EA and
ACR-MCR execution windows. This provides an M1 package power estimate,
not calibrated per-process electrical energy. The CPU power sampling
period (e.g. 1000ms) is longer than each 0.5s simulator test, so
repeat complete seed-block campaigns or execute long, isolated batches;
do NOT allocate one 1s power sample to a 0.18s optimizer. Include
timestamps, matched method order, thermal conditions, and independent
idle baseline. Report total observed package-power differences as
estimates only.

Actual host electrical energy in Joules would require a calibrated
external AC or DC wattmeter and synchronized interval integration,
with explicit baseline power subtraction and uncertainty. Such hardware
was not connected or used in this study.

The previously measured 11.7283J TX and 11.1273J RX in Grenoble
IoT-LAB experiment 459543 belong to TWO external M3 boards, not the
Apple M1 host optimizer.
