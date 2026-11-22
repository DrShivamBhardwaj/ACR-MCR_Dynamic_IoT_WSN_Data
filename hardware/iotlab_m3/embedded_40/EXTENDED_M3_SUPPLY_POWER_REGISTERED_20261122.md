# Frozen extended M3 original-decision-kernel electrical measurement

Registered BEFORE physical results, on 22 Nov 2026.

Same original Python source, input fixture, algorithm C kernel and
fixed NumPy RNG candidate trace as previous Grenoble 459572/459573.
Same real physical board M3-14, source-locked firmware and external
current/voltage/power profile acr_m3_active_power_20261122. The
controller is computed 20 identical times, with watchdog service after
each compute, as a **duration-increased instrumentation test**.
The run sleeps to approximately 120s after the 15s initial setup,
yielding enough physical OML readings to satisfy the preexisting
monitor requirement of >=25 samples and >=40s monotonic duration.

The two method sessions are executed sequentially on the same
physical board. Expected Python heads and mathematical objectives
cannot change. Accept only when all 20 C kernel invocations pass
absolute 1e-7 objective parity, the physical program ends, the
original UART is present, and the original control-node consumption
OML file passes independent schema, monotonic timestamp, consistency,
sample-count and physical power constraints. Preserve every failed
attempt and exact original source firmware SHA.

Registered descriptive physical endpoints: original supplied-board
total Joules integrated over the monitor's exact timestamps,
watts, mean voltage/current, and measured 20-call CPU elapsed time.
The monitoring interval may include bootstrap, UART, idle, radio
listeners and control node. It is NOT direct per-invocation processor
energy, and differences must not be interpreted as exact energy due
to ACR computation without synchronized idle baseline and external
instrument timing calibration.

Twenty repeated identical fixture computations are NOT twenty
independent topology seeds. No claim of generalisation, journal
acceptance, service superiority, full 40-node live original ACR-MCR,
or MacBook/Apple M1 host electrical energy is permitted.
