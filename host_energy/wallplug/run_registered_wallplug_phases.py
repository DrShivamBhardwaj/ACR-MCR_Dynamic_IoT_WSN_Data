#!/usr/bin/env python3
"""Run frozen original workloads ONLY if a real external AC wattmeter logs W."""
import argparse,datetime,hashlib,json,subprocess,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
SHA='3f134a8826525215f7cf2ff307bab3893c0d64b050f742bdc3c250b1c0302ea4'
PHASES=('IDLE','POINT-EA','ACR-MCR','ACR-MCR','POINT-EA','IDLE')
def stamp():return datetime.datetime.now(datetime.timezone.utc).isoformat()
def main():
    p=argparse.ArgumentParser()
    p.add_argument('--out-dir',required=True)
    p.add_argument('--external-meter-live',action='store_true')
    a=p.parse_args()
    if not a.external_meter_live:
        raise SystemExit('BLOCKED: external real AC power meter must be connected and logging actual W')
    if hashlib.sha256((ROOT/'acr_mcr_v2.py').read_bytes()).hexdigest()!=SHA:
        raise ValueError('Original model SHA256 mismatch')
    output=Path(a.out_dir);output.mkdir(exist_ok=False,parents=True)
    reg=dict(status='RUNNING_NO_POWER_RESULT',original_sha256=SHA,phases=[],
             meter_required=True)
    def save(): (output/'phase_boundaries.json').write_text(json.dumps(reg,indent=2)+'\n')
    save()
    for index,method in enumerate(PHASES,1):
        row=dict(phase=index,method=method,utc_start=stamp(),status='RUNNING')
        reg['phases'].append(row);save()
        if method=='IDLE':
            time.sleep(50)
            row.update(cases=0)
        else:
            worker=ROOT/'host_energy/power_batch_worker.py'
            py=ROOT.parent/'.venv/bin/python'
            res=subprocess.run([str(py),str(worker),'--method',method,
                  '--repeats','5'],capture_output=True,text=True)
            if res.returncode:
                row.update(status='FAILED',utc_end=stamp(),error=res.stderr[-1400:])
                save();raise RuntimeError('Original workload failed')
            obj=json.loads(res.stdout)
            if obj['cases']!=100 or obj['source_sha256']!=SHA:
                raise ValueError('Original workload incomplete')
            row.update(obj)
        row.update(status='FINISHED',utc_end=stamp());save()
        print('PHASE_COMPLETE',index,method,row['utc_end'],flush=True)
    reg['status']='PHASES_FINISHED_WAITING_FOR_EXTERNAL_METER_LOG'
    save()
    print('REGISTERED_PHASES_COMPLETED; REAL_WATTMETER_CSV_STILL_REQUIRED')
if __name__=='__main__':main()
