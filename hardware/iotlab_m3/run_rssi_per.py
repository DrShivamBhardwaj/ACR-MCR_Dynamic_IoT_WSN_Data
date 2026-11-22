"""Fresh ACR-MCR physical RSSI/packet-receipt vs configured TX power.
New four-board experimental run and logged power settings. This is NOT
external SNR calibration, NOT a 500B application transport validation, and
NOT the ACR routing algorithm. Reuses the existing verified RIOT tool binary,
but produces independent ACR-specific samples and no prior sample data.
"""
"""Execute FIT IoT-LAB official M3 radio characterization on four physical boards.

This is measured active 802.15.4 connectivity, RSSI/LQI and monitoring noise.
It is not ambient backscatter nor an absolute receiver-chain SNR calibration.
"""
import json,subprocess,pathlib,datetime,hashlib,time,sys
R=pathlib.Path(__file__).resolve().parent
CLI=pathlib.Path.home()/'Research/.iotlabcli-venv/bin/iotlab-experiment'
KEY=pathlib.Path.home()/'.ssh/id_ed25519_iotlab'
SSH=['ssh','-i',str(KEY),'-o','BatchMode=yes','-o','IdentitiesOnly=yes','-o','ConnectTimeout=15','sbhardwa@grenoble.iot-lab.info']
scp=['scp','-i',str(KEY),'-o','BatchMode=yes','-o','IdentitiesOnly=yes']
firmware='/senslab/users/sbhardwa/array_radio_measure/iotlabradio/riot/radio-characterization/bin/iotlab-m3/radio-characterization.elf'
name='ACR-MCR-Independent-M3-Radio-Power-Receipt'
exp=None;run=None

def action(stage,**kwargs):
 d={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stage':stage,**kwargs}
 (R/'m3_live_status.json').write_text(json.dumps(d,indent=2)+'\n');print(json.dumps(d),flush=True)

def remote(cmd,timeout=40):
 r=subprocess.run(SSH+[cmd],text=True,capture_output=True,timeout=timeout)
 if r.returncode:raise RuntimeError('remote failed: '+r.stderr[-500:])
 return r.stdout

def cli(*args):
 q=subprocess.run([str(CLI),*args],text=True,capture_output=True,timeout=40)
 if q.returncode:raise RuntimeError('CLI '+str(args)+' failed: '+q.stderr[-500:])
 return json.loads(q.stdout)

def save_remote():
 if run is None:return
 for suffix,path in [('official_logs','array_radio_measure/logs/'+str(exp)),('control_radio_monitor','.iot-lab/'+str(exp)+'/radio')]:
  try:
   q=subprocess.run(scp+['-r','sbhardwa@grenoble.iot-lab.info:'+path,str(run/suffix)],capture_output=True,text=True,timeout=120)
   (run/(suffix+'_copy_status.json')).write_text(json.dumps({'exit_code':q.returncode,'error':q.stderr[-500:]},indent=2)+'\n')
  except Exception as e:(run/(suffix+'_copy_status.json')).write_text(json.dumps({'error':repr(e)},indent=2)+'\n')
try:
 assert not cli('get','-e','--active'),'Existing active account experiment; will not interfere'
 print('remote firmware info',remote('sha256sum '+firmware).strip(),flush=True)
 submit=remote('iotlab-experiment submit -n '+name+' -d 18 -l grenoble,m3,2+14+150+350,'+firmware+',acr_m3_rssi_20261122')
 record=json.loads(submit);exp=int(record['id'])
 run=R/'runs'/str(exp);run.mkdir(parents=True,exist_ok=False)
 (run/'submission.json').write_text(json.dumps(record,indent=2)+'\n')
 (run/'firmware.sha256').write_text(remote('sha256sum '+firmware).strip()+'\n')
 action('reserved',experiment=exp)
 for i in range(80):
  meta=cli('get','-i',str(exp),'-p');(run/'experiment.json').write_text(json.dumps(meta,indent=2)+'\n')
  if meta.get('state')=='Running':break
  if meta.get('state') in ('Stopped','Terminated','Error'):raise RuntimeError('Reservation ended: '+str(meta.get('state')))
  time.sleep(3)
 else:raise RuntimeError('Experiment not Running within wait window')
 dep=cli('get','-i',str(exp),'-d');(run/'deployment.json').write_text(json.dumps(dep,indent=2)+'\n')
 if len(dep.get('0',[]))!=4:raise RuntimeError('Firmware deploy failure '+str(dep))
 action('official_radio_characterization_running',experiment=exp)
 script='cd ~/array_radio_measure && PYTHONPATH=./pydeps python3 ./iotlab-radio -i '+str(exp)+' --channel 11 --txpower -17 -9 0 3 --nb-packet 100 --packet-size 50 --delay 1 --timeout 7'
 with (run/'radio_stdout.log').open('w') as o,(run/'radio_stderr.log').open('w') as e:
  q=subprocess.run(SSH+[script],stdout=o,stderr=e,timeout=920)
 (run/'radio_command.txt').write_text(script+'\n')
 if q.returncode:raise RuntimeError('Official tool exited '+str(q.returncode)+'; inspect stderr')
 action('official_radio_characterization_complete',experiment=exp)
except Exception as e:
 action('error',experiment=exp,error=repr(e));raise
finally:
 if exp is not None:
  try:
   action('experiment_finishing',experiment=exp)
   print('stop',cli('stop','-i',str(exp)),flush=True)
  except Exception as e:print('STOP FAILED',repr(e),flush=True)
  action('reservation_stopped',experiment=exp)
  try:
   # Control-node RSSI monitoring files flush when the reservation stops.
   time.sleep(8)
   action('exporting_original_raw_monitor_and_radio_logs',experiment=exp)
   save_remote()
   action('raw_monitor_and_radio_export_complete',experiment=exp)
  except Exception as e:
   print('EXPORT PROBLEM',repr(e),flush=True)
