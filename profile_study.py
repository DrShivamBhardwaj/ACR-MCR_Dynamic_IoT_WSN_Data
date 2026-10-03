"""Run sequentially after the benchmark for an isolated timing measurement."""
from pathlib import Path
from dataclasses import replace
import csv,json,platform,sys
import numpy as np
from acr_mcr_v2 import Simulator,Config

root=Path(__file__).resolve().parent
rows=[]
for n in [40,80,120]:
    for method in ['POINT-EA','ACR-MCR']:
        for seed in range(9500,9505):
            r=Simulator(seed,'S5',method,replace(Config(),nodes=n)).run()
            rows.append(dict(nodes=n,method=method,seed=seed,
                decision_stage_ms_per_round=1000*r['controller_seconds']/r['rounds'],
                simulation_seconds=r['simulation_seconds'],searches=r['searches']))
        print('Profiled',n,method,flush=True)
with (root/'analysis/timing_profile.csv').open('w',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
cpu=next((x.split(':',1)[1].strip() for x in Path('/proc/cpuinfo').read_text().splitlines() if x.startswith('model name')),'unknown')
(root/'analysis/timing_environment.json').write_text(json.dumps(dict(cpu=cpu,platform=platform.platform(),
    python=sys.version,numpy=np.__version__,workers=1,blas_threads=1,scope='head search and route construction; excludes prediction update and radio execution'),indent=2))
