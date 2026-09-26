# ns-3 IEEE 802.15.4 mechanism validation

The packet-level validation was executed with ns-3.48 on macOS (Apple M1) using the lr-wpan module. The experiment compares a central point-estimate path with a spatially separated risk-avoiding path under a localized burst interferer. This is a mechanism validation of the risk gate, not a full ns-3 implementation of ACR-MCR.

Compile on a Homebrew ns-3 installation:

```bash
MODS="ns3-core ns3-network ns3-mobility ns3-lr-wpan ns3-spectrum ns3-propagation"
c++ -std=c++20 acr_route_validation.cc -o acr_route_validation $(pkg-config --cflags $MODS) $(pkg-config --libs $MODS | sed 's/-linterface_libs-NOTFOUND//g')
```

A typical paired run is:

```bash
./acr_route_validation --seed=1 --risk=0 --jamPower=-20 --jamInterval=0.006 --riskY=22 --exponent=3.5
./acr_route_validation --seed=1 --risk=1 --jamPower=-20 --jamInterval=0.006 --riskY=22 --exponent=3.5
```

For the stochastic 30-seed batch, jammer power was varied from -24 to -16 dBm and jammer interval from 5 to 9 ms using the same disturbance parameters for both paired routes in each seed. A 20-seed control used negligible jammer power (-80 dBm).
