"""Execute the locked protocol; save raw data before any inferential analysis."""
import os
os.environ['OPENBLAS_NUM_THREADS']='1'
os.environ['OMP_NUM_THREADS']='1'
import csv,gzip,hashlib,json,platform,sys,time
from concurrent.futures import ProcessPoolExecutor,as_completed
from dataclasses import asdict,replace
from datetime import datetime,timezone
from pathlib import Path
import numpy as np
from acr_mcr_v2 import Simulator,Config,METHODS

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'results'

def jobs():
    base=Config()
    items=[]
    def add(group,seeds,scenarios,methods,config):
        for seed in seeds:
            for sc in scenarios:
                for method in methods:
                    tag=f'{group}_N{config.nodes}_B{config.probes}_K{config.fixed_heads}_{sc}_{seed}_{method}'
                    items.append(dict(group=group,seed=seed,scenario=sc,method=method,config=asdict(config),tag=tag))
    add('main',range(1000,1030),['S1','S2','S3','S4','S5'],list(METHODS),base)
    add('stationary',range(1000,1010),['S0'],list(METHODS),base)
    for n in (80,120): add('scale',range(2000,2010),['S5'],['POINT-EA','ACR-MCR'],replace(base,nodes=n))
    for b in (0,1,2): add('probes',range(3000,3010),['S5'],['POINT-EA','ACR-MCR'],replace(base,probes=b))
    for k in (4,5,6): add('heads',range(4000,4010),['S5'],['POINT-EA','ACR-MCR'],replace(base,nodes=60,fixed_heads=k))
    return items

def write_csv(path,rows):
    if not rows:return
    with gzip.open(path,'wt',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

def execute(job):
    diag=job['group']=='main' and job['seed']==1000
    sim=Simulator(job['seed'],job['scenario'],job['method'],Config(**job['config']),diag)
    result=sim.run();result.update(group=job['group'],run_id=job['tag'])
    write_csv(OUT/'rounds'/f"{job['tag']}.csv.gz",sim.rows)
    if diag:write_csv(OUT/'links'/f"{job['tag']}.csv.gz",sim.link_logs)
    return result

def main():
    for sub in ('rounds','links'): (OUT/sub).mkdir(parents=True,exist_ok=True)
    manifest_path=OUT/'manifest.json'
    if manifest_path.exists():raise RuntimeError('Refusing to overwrite a completed or partial locked study.')
    run_jobs=jobs()
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in ROOT.glob('*.py')}
    hashes['PROTOCOL.md']=hashlib.sha256((ROOT/'PROTOCOL.md').read_bytes()).hexdigest()
    manifest=dict(started_utc=datetime.now(timezone.utc).isoformat(),python=sys.version,numpy=np.__version__,
        platform=platform.platform(),workers=8,source_sha256=hashes,job_count=len(run_jobs),jobs=run_jobs)
    manifest_path.write_text(json.dumps(manifest,indent=2))
    allrows=[];start=time.perf_counter()
    with (OUT/'raw_results.jsonl').open('w') as log:
        with ProcessPoolExecutor(max_workers=8) as executor:
            futures={executor.submit(execute,j):j for j in run_jobs}
            for future in as_completed(futures):
                row=future.result();allrows.append(row)
                log.write(json.dumps(row,allow_nan=True)+'\n');log.flush()
                if len(allrows)%50==0 or len(allrows)==len(run_jobs):
                    print(f"Completed {len(allrows)}/{len(run_jobs)}; elapsed {time.perf_counter()-start:.1f}s",flush=True)
    allrows.sort(key=lambda r:r['run_id'])
    with (OUT/'raw_results.csv').open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(allrows[0]));w.writeheader();w.writerows(allrows)
    manifest['completed_utc']=datetime.now(timezone.utc).isoformat()
    manifest['elapsed_seconds']=time.perf_counter()-start
    manifest_path.write_text(json.dumps(manifest,indent=2))
    print('Study complete',flush=True)

if __name__=='__main__':main()
