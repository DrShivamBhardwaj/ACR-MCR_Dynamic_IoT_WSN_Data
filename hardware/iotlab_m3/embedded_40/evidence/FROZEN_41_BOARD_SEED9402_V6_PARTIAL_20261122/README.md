# Original on-M3 V6 corrected-flash attempt, preserve both raw arms

Protocol: REGISTERED_V6_PHYSICAL_FLASH_RECOVERY_20261122.md,
seed9402 S5 round20, original frozen 40-node point/risk kernel,
unchanged V5 source firmware, 40 sources plus one M3 sink,
3 rounds, 500B samples, 120 nominal demand opportunities per arm.

POINT-EA Grenoble experiment **459607**: 41/41 IoT-LAB firmware
flashes succeeded, 41 UART streams, 41 ENERGEST, 120/120 radio
control installations, 47/120 full 500B sink completions,
source-locked sink kernel and packet-capture validation PASS.

ACR-MCR experiment **459611**: 41/41 firmware flashes succeeded
but **four source UART streams were missing**. Its 50/120
sink receipts are DESCRIPTIVE ONLY and must not enter the
registered complete physical comparison. The missing original
physical UART included nodes 203,204,205 and the old M3-215
address that should have been replaced by M3-196. A concurrently
running independent IoT-LAB workflow appears to have overwritten
the frontend SHARED physical_layout.json during the ACR capture.
The original IoT-LAB firmware deployment metadata *does* confirm
the new board 196 in the reserved group. See exact input.
Never infer 41-stream validation from 37 logs or claim 500ms
timeliness from unsynchronised source clocks.

A separately pre-registered V7 capture repair pins the
unique physical layout filename and exact SHA before the
next ACR-only diagnostic repeat. No original data from this
failed developer run were deleted.
