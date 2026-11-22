# New ACR-MCR physical M3 transport and electrical-power run 459543

Location: Grenoble M3-14 TX and M3-15 RX, 22 Nov 2026.
All 100 offered 500-byte source samples, each carried as eight CSMA frames
(64*7+52 bytes), were captured from sample 0 through 99. There were
800/800 matching send callbacks and received-fragment logs, followed by
100/100 content-verified full 500-byte reassemblies. No source MAC
failure or recorded content corruption in this ONE link/time block.

This experiment used a newly created physical control-node monitor
profile: acr_m3_active_power_20261122, external DC supply, measurement
period 8244 us, average 128. Each OML file includes original control
node timestamps and physically measured current, voltage and power;
physical_power_audit.json integrates these samples as measured using the
trapezoidal rule. M3-14 107.661 s ~11.7283 J total supplied device
energy; M3-15 109.162 s ~11.1273 J total supplied device energy.
Those are full-board intervals including CPU, radio, idle and serial,
NOT radio-only or energy attributable solely to transmitted frames.

TX firmware SHA256:
c82c38e4ea192c05fd9af385d7176165703180d2264bcec2ab7266645e864534
RX firmware SHA256:
f57d798f86560f80fe83fb5768fcd5573ed43e0baee76832df3c1e251da04d74

Firmware source is hardware/iotlab_m3/acr_phy_app.h in the parent
repository, with C compile setting ACR_PHY_START_DELAY_S=25 and
ENERGEST_CONF_ON=1. The delayed 25s start ensures complete capture
of sample 0. This hardware source is a two-board 500-byte transport
test, not the complete 40-node ACR-MCR controller.

No physical receiver noise measurement, calibrated SNR or PHY-PER
curve was established. The RX raw PHY_RSSI/PHY_ED register snapshots
are uncalibrated register data, not physical SNR. Current/voltage
monitor values are real measured externally supplied device totals.
Host Python controller power and full network control energy are
NOT in this data. No field generalisation is asserted.
