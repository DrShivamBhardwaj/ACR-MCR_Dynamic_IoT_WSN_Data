#!/usr/bin/env python3
"""Fail-closed timestamp-integrated AC wattmeter readings, no synthetic Joules."""
import argparse,csv,datetime,hashlib,json,math,statistics
from pathlib import Path
SOURCE_SHA='3f134a8826525215f7cf2ff307bab3893c0d64b050f742bdc3c250b1c0302ea4'
ORDER=('IDLE','POINT-EA','ACR-MCR','ACR-MCR','POINT-EA','IDLE')
def sha(f):return hashlib.sha256(f.read_bytes()).hexdigest()
def epoch(s):
    z=datetime.datetime.fromisoformat(s.replace('Z','+00:00'))
    if z.tzinfo is None:raise ValueError('Missing timezone: '+s)
    return z.timestamp()
def integrate(power,start,end):
    if start<power[0][0] or end>power[-1][0] or end-start<20:
        raise ValueError('AC meter does not cover an entire useful phase')
    def pw(t):
        for (a,va),(b,vb) in zip(power,power[1:]):
            if a<=t<=b:
                if b-a>3.0:raise ValueError('Cannot interpolate over missing AC samples')
                return va+(vb-va)*(t-a)/(b-a)
        raise ValueError('AC sample interval missing')
    trimmed=[(start,pw(start))]+[(t,w) for t,w in power if start<t<end]+[(end,pw(end))]
    if len(trimmed)<22:raise ValueError('Insufficient actual meter samples')
    total=0.
    for (a,wa),(b,wb) in zip(trimmed,trimmed[1:]):
        if not 0<b-a<=3:raise ValueError('Meter sample cadence failure')
        total+=(b-a)*(wa+wb)/2
    return total
def validate(folder):
    folder=Path(folder)
    docs=[folder/x for x in ('phase_boundaries.json','meter_power.csv','meter_identity.json')]
    if any(not x.is_file() for x in docs):
        raise RuntimeError('NO_EXTERNAL_METER_DATA: must not invent wall-plug Joules')
    reg=json.loads(docs[0].read_text());meter=json.loads(docs[2].read_text())
    needed=('meter_model','meter_serial','real_power_unit','calibration_file',
            'calibration_file_sha256','clock_sync_record')
    if any(not meter.get(k) for k in needed):
        raise ValueError('Missing real instrument identity, calibration or clock record')
    if meter['real_power_unit']!='W':raise ValueError('Need real AC watts, not VA or adapter rating')
    certificate=folder/meter['calibration_file']
    if not certificate.exists() or sha(certificate)!=meter['calibration_file_sha256']:
        raise ValueError('Calibration document missing or SHA256 incorrect')
    if reg['original_sha256']!=SOURCE_SHA or reg['status']!='PHASES_FINISHED_WAITING_FOR_EXTERNAL_METER_LOG':
        raise ValueError('Original simulator workload incomplete')
    if len(reg['phases'])!=6 or tuple(p['method'] for p in reg['phases'])!=ORDER:
        raise ValueError('Nonregistered phase order')
    data=[]
    with docs[1].open(newline='') as f:
        rd=csv.DictReader(f)
        if not {'timestamp_utc','power_W'}.issubset(rd.fieldnames or []):
            raise ValueError('External AC data requires timestamp_utc,power_W')
        for line in rd:
            t=epoch(line['timestamp_utc']);power=float(line['power_W'])
            if not 0<=power<=500 or not math.isfinite(power):
                raise ValueError('Impossible actual AC power reading')
            data.append((t,power))
    if len(data)<100 or any(a[0]>=b[0] for a,b in zip(data,data[1:])):
        raise ValueError('Incomplete/unsorted actual wattmeter log')
    phases=[]
    for p in reg['phases']:
        if p['status']!='FINISHED':raise ValueError('Incomplete phase')
        if p['method']!='IDLE' and (p.get('cases')!=100 or p.get('source_sha256')!=SOURCE_SHA):
            raise ValueError('Incomplete original simulator work')
        start,end=epoch(p['utc_start']),epoch(p['utc_end'])
        total=integrate(data,start,end)
        phases.append(dict(method=p['method'],gross_AC_input_J=total,
                   interval_s=end-start,mean_AC_W=total/(end-start),
                   full_simulator_cases=p.get('cases',0)))
    idle0=phases[0]['mean_AC_W'];idle5=phases[5]['mean_AC_W']
    for i in range(1,5):
        phase=phases[i]
        interpolated=idle0+(idle5-idle0)*i/5
        phase['baseline_adjusted_incremental_AC_J']=phase['gross_AC_input_J']-interpolated*phase['interval_s']
        phase['incremental_AC_J_per_full_original_simulator_case']=phase['baseline_adjusted_incremental_AC_J']/100
    report=dict(status='AC_METER_OBSERVATIONS_INTEGRATED_CALIBRATION_AUTHENTICITY_REQUIRES_REVIEW',
       original_sha256=SOURCE_SHA,meter_model=meter['meter_model'],
       serial=meter['meter_serial'],calibration_sha256=sha(certificate),
       calibration_authenticity_not_independently_verified=True,
       actual_external_AC_power_samples=len(data),phases=phases,
       caveat='Gross real AC input contains charger loss and all laptop loads; adjusted energy is not exclusive to optimizer. Two phases per method are insufficient for inferential CI.')
    dest=folder/'real_wallplug_energy_J_PENDING_CALIBRATION_REVIEW.json'
    dest.write_text(json.dumps(report,indent=2)+'\n')
    print('REAL_AC_POWER_INTEGRATED_PENDING_INDEPENDENT_METER_CERTIFICATE_REVIEW',dest)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--study-dir',required=True)
    a=p.parse_args();validate(a.study_dir)
