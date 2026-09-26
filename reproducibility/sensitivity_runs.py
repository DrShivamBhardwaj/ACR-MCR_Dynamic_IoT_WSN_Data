from pathlib import Path
import pandas as pd
from acr_mcr import WSNSimulator
out=Path(__file__).parent/'results_submission'/'sensitivity_S5.csv'
rows=[]
settings=[]
for alpha in [0.05,0.10,0.15]: settings.append(('alpha',alpha,dict(conformal_alpha=alpha)))
for window in [100,220,400]: settings.append(('window',window,dict(conformal_window=window)))
for cvar in [0.0,0.05,0.10,0.20]: settings.append(('cvar_weight',cvar,dict(cvar_weight=cvar)))
for name,val,kw in settings:
 for seed in range(5):
  r=WSNSimulator(n_nodes=40,rounds=80,seed=seed,scenario='S5',method='ACR-MCR',**kw).run()
  r['parameter']=name; r['value']=val; rows.append(r)
  print(name,val,'seed',seed,flush=True)
pd.DataFrame(rows).to_csv(out,index=False)
