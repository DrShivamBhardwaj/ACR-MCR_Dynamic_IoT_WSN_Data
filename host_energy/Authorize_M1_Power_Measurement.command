#!/bin/zsh
# This script is intended to be run by the Mac OWNER in a local Terminal.
# Never supply the administrator password to ChatGPT or a remote agent.
set -euo pipefail
ROOT="/Users/shivambhardwaj/research/ACR_MCR_Recovery_20261122"
WORK="$ROOT/data/host_energy"
PY="$ROOT/.venv/bin/python"
echo ""
echo "ACR-MCR: local macOS administrator-approved estimated CPU power trace"
echo "Original source is immutable, six frozen stages, raw traces retained."
echo "Your Mac will request local administrator authentication."
echo "Estimated power is NOT a calibrated wall-plug energy meter."
echo ""
if [[ ! -x "$PY" ]];then echo "Python virtual environment missing";exit 2;fi
"$PY" "$WORK/collect_m1_power_authorized.py" --preflight
/usr/bin/sudo -v
/usr/bin/sudo "$PY" "$WORK/collect_m1_power_authorized.py" --repeats 5
/usr/bin/sudo /usr/sbin/chown -R "$(id -un):staff" "$WORK/authorized_m1_power_runs"
"$PY" "$WORK/analyze_authorized_m1_power.py" --latest
echo ""
echo "Local Mac authorization and power data collection completed."
echo "The evidence is available in host_energy/authorized_m1_power_runs."
echo "It is not automatically a calibrated electrical meter measurement."
echo "You may close this Terminal window."
