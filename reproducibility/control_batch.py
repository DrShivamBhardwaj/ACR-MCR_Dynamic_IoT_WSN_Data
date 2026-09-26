import argparse
from pathlib import Path
import pandas as pd
from acr_mcr import WSNSimulator
p=argparse.ArgumentParser();p.add_argument('--start',type=int,required=True);p.add_argument('--end',type=int,required=True);a=p.parse_args()
out=Path(__file__).parent/'results_submission'/'control_S0_20seed.csv'; old=pd.read_csv(out) if out.exists() else pd.DataFrame(); done=set(zip(old.seed.astype(int),old.method.astype(str))) if len(old) else set(); rows=old.to_dict('records') if len(old) else []
for seed in range(a.start,a.end):
 for m in ['POINT-EA','SCP-EA','ACP-EA','ACR-NOCVAR','ACR-MCR']:
  if (seed,m) not in done: rows.append(WSNSimulator(n_nodes=40,rounds=80,seed=seed,scenario='S0',method=m).run())
 pd.DataFrame(rows).to_csv(out,index=False); print('seed',seed,'rows',len(rows),flush=True)
