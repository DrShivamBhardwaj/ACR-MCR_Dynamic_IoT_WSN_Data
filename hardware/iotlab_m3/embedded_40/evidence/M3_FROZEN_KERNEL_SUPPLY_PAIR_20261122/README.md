# Physical Grenoble M3 supply-energy experiments, deterministic original kernel

POINT-EA M3-14 experiment459581 and ACR-MCR M3-14 experiment459584.
Same original simulator seed9401 S1 round20, 20 repeats per method.
Fixed NumPy candidate/stress fixtures held in FLASH. M3 UART parity
shows identical original Python-selected head IDs and objective within
the registered <=100 nanounit gate. Both actual M3 control-node OML
files contain 72 physical supplied-power/current/voltage samples.

POINT-EA: 0.106953 W, 16.030837 J over 149.887s.
ACR-MCR: 0.129357 W, 19.388274 J over 149.882s.
These are externally supplied entire M3 board energies, with idle,
radio, and CPU contributions; NOT isolated decision Joules, and NOT
Apple M1 host energy. Single independently frozen seed and one
physical session per method cannot support causal energy difference
or independent confidence intervals. No power difference inference
is warranted absent balanced repeats and idle correction. Neither
full physical 40-node adaptive feedback nor 500ms service outcomes
were tested in these one-board kernel sessions.
