import argparse, json
from pathlib import Path
import pandas as pd
from acr_mcr import WSNSimulator

p=argparse.ArgumentParser(); p.add_argument('--start',type=int,required=True); p.add_argument('--end',type=int,required=True)
p.add_argument('--out',default='results_submission/raw_20seed.csv'); p.add_argument('--nodes',type=int,default=40); p.add_argument('--rounds',type=int,default=80)
a=p.parse_args()
out=Path(__file__).parent/a.out; out.parent.mkdir(parents=True,exist_ok=True)
old=pd.read_csv(out) if out.exists() else pd.DataFrame()
done=set(zip(old.seed.astype(int),old.scenario.astype(str),old.method.astype(str))) if len(old) else set()
rows=old.to_dict('records') if len(old) else []
methods=['POINT-EA','SCP-EA','ACP-EA','ACR-NOCVAR','ACR-MCR']
for seed in range(a.start,a.end):
  for sc in ['S1','S2','S3','S4','S5']:
    for m in methods:
      if (seed,sc,m) in done: continue
      r=WSNSimulator(n_nodes=a.nodes,rounds=a.rounds,seed=seed,scenario=sc,method=m).run()
      rows.append(r); done.add((seed,sc,m))
  pd.DataFrame(rows).to_csv(out,index=False)
  print('completed seed',seed,'rows',len(rows),flush=True)
