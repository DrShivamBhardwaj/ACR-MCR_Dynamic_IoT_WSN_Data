import argparse, json, os
from pathlib import Path
import numpy as np
import pandas as pd
from acr_mcr import WSNSimulator, METHODS


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--seeds', type=int, default=8)
    ap.add_argument('--nodes', type=int, default=60)
    ap.add_argument('--rounds', type=int, default=140)
    ap.add_argument('--out', type=str, default='results')
    args = ap.parse_args()
    out = Path(args.out); out.mkdir(parents=True, exist_ok=True)
    scenarios = ['S0','S1','S2','S3','S4','S5']
    methods = list(METHODS.keys())
    rows=[]
    for s in scenarios:
        for m in methods:
            for seed in range(args.seeds):
                sim=WSNSimulator(n_nodes=args.nodes, rounds=args.rounds, seed=seed, scenario=s, method=m)
                rows.append(sim.run())
    df=pd.DataFrame(rows)
    df.to_csv(out/'raw_results.csv', index=False)
    metrics=['PDR','mean_delay','energy_consumed','final_alive','FND','HND','risk_violation_rate','optimizer_calls','etx_coverage','delay_coverage']
    summary=df.groupby(['scenario','method'])[metrics].agg(['mean','std']).reset_index()
    summary.columns=['_'.join([str(x) for x in c if x!='']).rstrip('_') if isinstance(c,tuple) else c for c in summary.columns]
    summary.to_csv(out/'summary.csv', index=False)
    # Relative comparison of ACR-MCR vs POINT-EA per scenario.
    comp=[]
    for s in scenarios:
        a=df[(df.scenario==s)&(df.method=='ACR-MCR')]
        b=df[(df.scenario==s)&(df.method=='POINT-EA')]
        if len(a) and len(b):
            comp.append({
                'scenario':s,
                'PDR_delta_pct':100*(a.PDR.mean()-b.PDR.mean())/max(1e-9,b.PDR.mean()),
                'delay_delta_pct':100*(a.mean_delay.mean()-b.mean_delay.mean())/max(1e-9,b.mean_delay.mean()),
                'risk_violation_delta_pct':100*(a.risk_violation_rate.mean()-b.risk_violation_rate.mean())/max(1e-9,b.risk_violation_rate.mean()),
                'optimizer_call_delta_pct':100*(a.optimizer_calls.mean()-b.optimizer_calls.mean())/max(1e-9,b.optimizer_calls.mean()),
                'energy_delta_pct':100*(a.energy_consumed.mean()-b.energy_consumed.mean())/max(1e-9,b.energy_consumed.mean()),
            })
    pd.DataFrame(comp).to_csv(out/'acr_vs_point.csv', index=False)
    print(summary.to_string(index=False))

if __name__=='__main__':
    main()
