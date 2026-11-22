# ACR-MCR 500-byte physical radio-transport pilot

Date: 22 November 2026. Study is a fresh experiment belonging to ACR-MCR,
not prior user projects or historical IoT-LAB runs.

Experimental provenance:
- IoT-LAB: Grenoble, Saclay rejected because saved SSH host key changed.
  Grenoble frontend already passed strict known-host verification.
- Newly submitted experiment: **459541**, Grenoble M3-14 sender, M3-15
  receiver; two separate binaries, role 1 and role 2.
- Target: IoT-LAB M3 AT86RF231, Contiki-NG IoT-LAB port.
- Fresh source: acr_phy_app.h, acr_phy_tx.c, acr_phy_rx.c, Makefile.
- TX firmware SHA256:
  7a9e641bd2a2f83ad3ae826ef42781b8e1e0ccb68f5ecd785f9ba2334bc7099c
- RX firmware SHA256:
  e47a67419812a4651c2975f025515736092a296cd42e0c05e30d0a875fa4901c
- Sender schedules 100 application samples x 500 bytes. Each is transmitted
  as eight MAC frames carrying 64,64,64,64,64,64,64,52 application bytes.
- Receiver reconstructs all 500 bytes and verifies deterministic full
  payload content. Sender records radio MAC callback status/attempts;
  receiver records actual fragment receipts and any full reassembly.
- Firmware prints Contiki ENERGEST counters where provided by board/driver.
- PHY_RSSI and PHY_ED_LEVEL registers are read as raw register bytes.
  **These are not calibrated RSSI, noise power or SNR in dB**.
- Backend capture code checks verified 500-byte payloads and stores raw
  source and receiver UART lines, firmware hashes, and experiment metadata.
- This hardware run does not execute ACR-MCR clustering, adaptive conformal
  control or the full 40-node distributed protocol. It solely characterizes
  one physical link's 500-byte fragment transfer using the required frame
  structure. There is no permitted extrapolation to a calibrated 40-node PHY.

At current creation time the experiment has been submitted, not yet
accepted as a successful result. Any missing/partial trace must remain
failed or incomplete rather than being filled in.

## Still needed for external calibration

[NEED SOURCE] Validated register-to-RSSI/ED conversion for AT86RF231,
calibrated noise floor and SNR under measured physical conditions. The
legacy M3 rf231 driver does not implement RADIO_PARAM_LAST_RSSI or
RADIO_PARAM_TXPOWER, so neither a SNR–PER function nor a transmit-power
sweep in dBm can be claimed from these raw registers.

[NEED SOURCE] Measured device currents and voltage in CPU, idle/LPM,
radio TX and radio listen modes. ENERGEST ticks alone do not determine
physical Joules. An absolute energy comparison must not be fabricated
from unverified current values.

[NEED SOURCE] Multi-node physical deployment of actual closed-loop
ACR-MCR controller, including distributed control and telemetry costs.
The two-board run provides transport evidence only.


## Independently completed new physical evidence, 22 November 2026

- Initial Grenoble reservation 459541 was stopped when the serial
  frontend capture code referenced the wrong site/node IDs. It
  produced no scientific measurement; do not reuse it.
- Fresh Grenoble experiment 459542 captured TX/RX logs only for source
  sample IDs 8-99. Strict audit PASS for 92 matched, byte-verified
  500-byte samples and 736 captured MAC fragments. Source firmware
  reported 100 samples/800 ACKs overall, but missing first eight
  UART samples prohibit calculating complete-cohort PER.
- Fresh Grenoble experiment **459543** used a 25s firmware start delay
  and captured all 100 x 500B application samples, all 800 MAC
  fragment receptions and callbacks, with 100 payload-integrity
  checks successful. Strict audit PASS. One link/time block only.
- This third reservation used actual IoT-LAB monitoring profile
  acr_m3_active_power_20261122 for physical voltage/current/power.
  Monitor OML time integration PASS: M3-14 TX delivered 11.7283 J
  over 107.661 s; M3-15 RX 11.1273 J over 109.162 s. Those are
  externally supplied full-device energies, not per-packet power.
- All original serial and OML traces, SHA256 manifests, independent
  audit outputs and firmware source are retained under
  hardware/iotlab_m3/evidence/459542 and evidence/459543.
- Calibrated physical SNR–PER, multi-condition interference,
  embedded optimizer CPU power and 40-node physical algorithm
  validation remain **unperformed**. Do not use the new two-board
  data as proof of those claims.
