"""Independently verify FIT IoT-LAB official M3 radio-characterization records.

4 M3 transmitters, powers {-17,-9,0,+3}, 100 packet numbers each,
3 candidate receivers per transmitter: 1600 offered and 4800 link trials.
RSSI is packet receiver reported; control-node channel-14 median is
an environmental reference only, NOT calibrated PHY SNR.
"""
from pathlib import Path
from collections import defaultdict,Counter
import csv,json,math,statistics,hashlib,sys
R=Path(__file__).resolve().parent
exp=sys.argv[1] if len(sys.argv)>1 else '458257';run=R/'runs'/exp
path=next((run/'official_logs').glob('*/config.json'),None)
assert path, 'Official radio logs missing'
base=path.parent
config=json.loads(path.read_text());nodes=[int(x.split('-')[1]) for x in config['nodes']]
assert sorted(nodes)==[2,14,150,350] and config['power']==[-17,-9,0,3] and config['nb_packet']==100 and config['channel']==[11]
def load(name):return list(csv.DictReader((base/(name+'-logs.csv')).open()))
send=load('send');rec=load('recv');err=load('error')
assert len(send)==1600 and len(rec)==4800 and len(err)==48,(len(send),len(rec),len(err))
assert len({(x['channel'],x['power'],x['tx_node'],x['pkt_num']) for x in send})==1600
assert len({(x['channel'],x['power'],x['rx_node'],x['tx_node'],x['pkt_num']) for x in rec})==4800
assert all(x['tx_node']!=x['rx_node'] for x in rec)
assert all(x['pkt_send']=='1' for x in send),'Failed send API calls; denominator must be reassessed'
assert set(x['tx_node'] for x in send)==set(map(str,nodes))
assert set(x['rx_node'] for x in rec)==set(map(str,nodes))
for x in rec:
 assert x['rssi']=='0' and x['lqi']=='0' or (int(x['rssi'])<0 and int(x['lqi'])>0)
by=defaultdict(list)
for x in rec:by[(int(x['power']),int(x['tx_node']),int(x['rx_node']))].append(x)
assert len(by)==48 and all(len(v)==100 for v in by.values())

def wilson(s,n):
 z=1.95996398454;p=s/n;d=1+z*z/n;mid=(p+z*z/(2*n))/d;rad=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d;return mid-rad,mid+rad
rows=[]
for (power,tx,rx),v in sorted(by.items()):
 valid=[int(x['rssi']) for x in v if x['rssi']!='0'];n=len(valid);lo,hi=wilson(n,len(v))
 rows.append({'power_dbm_setting':power,'tx_m3':tx,'rx_m3':rx,'offered':len(v),'received':n,'delivery_fraction':n/len(v),'idealized_wilson95_low':lo,'idealized_wilson95_high':hi,'median_rssi_dbm_of_received':statistics.median(valid) if valid else '', 'mean_rssi_dbm_of_received':statistics.mean(valid) if valid else '', 'rssi_observed_only_on_reception':True})
assert sum(x['received'] for x in rows)==sum(x['rssi']!='0' for x in rec)
with (run/'m3_link_characterization.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,list(rows[0]),lineterminator='\n');w.writeheader();w.writerows(rows)
per_power=[]
for power in sorted(config['power']):
 r=[x for x in rows if x['power_dbm_setting']==power];n=sum(x['offered'] for x in r);s=sum(x['received'] for x in r);lo,hi=wilson(s,n);valid=[int(x['rssi']) for x in rec if int(x['power'])==power and x['rssi']!='0']
 per_power.append({'power_dbm_setting':power,'receiver_link_trials':n,'successful_receives':s,'delivery_fraction':s/n,'idealized_wilson95_low':lo,'idealized_wilson95_high':hi,'median_packet_rssi_dbm_received_only':statistics.median(valid) if valid else None,'n_links':len(r)})
with (run/'m3_aggregate_power.csv').open('w',newline='') as f:
 w=csv.DictWriter(f,list(per_power[0]),lineterminator='\n');w.writeheader();w.writerows(per_power)
# Count RX/PHY parser error flags without claiming that all missing frames were corrupted.
errors={k:sum(int(x[k]) for x in err) for k in ['generic','magic_number','crc','control']}
# Parse the separately monitored radio reference channel (if files transferred in full).
noise=[];folder=run/'control_radio_monitor_complete/radio'
if not folder.exists():folder=run/'control_radio_monitor'
for p in sorted(folder.glob('m3_*.oml')):
 valid14=[];valid11=[];meta={}
 for line in p.open(errors='replace'):
  cols=line.split()
  if len(cols)!=7 or cols[1]!='2':continue
  try:ch=int(cols[5]);value=int(cols[6])
  except ValueError:continue
  if ch==14:valid14.append(value)
  elif ch==11:valid11.append(value)
 if valid14:
  noise.append({'board':p.stem,'channel14_samples':len(valid14),'median_channel14_reference_rssi_dbm':statistics.median(valid14),'channel11_samples':len(valid11),'median_channel11_rssi_dbm':statistics.median(valid11) if valid11 else None,'scope':'Control-node radio power reading; channel14 is different from traffic channel11 and not calibrated input SNR'})
if noise:
 with (run/'m3_reference_channel_noise.csv').open('w',newline='') as f:
  w=csv.DictWriter(f,list(noise[0]),lineterminator='\n');w.writeheader();w.writerows(noise)
manifest={'experiment':int(exp),'experiment_label':'ACR-MCR-specific fresh RIOT M3 radio physical characterization','physical_nodes':nodes,'channel':11,'power_dbm_configured':config['power'],'offered_phy_packets':len(send),'candidate_link_receptions':len(rec),'unique_successful_received':sum(x['received'] for x in rows),'receiver_link_failure_count':sum(x['offered']-x['received'] for x in rows),'parser_errors':errors,'per_power':per_power,'receivers_reference_channel':noise,'status':'Source/RX packet-number consistency verified (M3 active radio, not ambient backscatter or absolute SNR calibration)','limits':['Broadcast raw M3 frames, not CAFE-HAB packets or ambient-backscatter frames','No ACK in this broadcast characterization; packet reception is post-CRC, not raw one-bit BER','Control-node channel14 reference noise differs from traffic channel11, and receiver gain calibration uncertainty is unknown','Per-link medians computed only from received packets: selection bias in low-PDR links','Repeatability is restricted to one time block per configuration, despite 100 packets within block','Confidence intervals assume independent frames and are idealized; no across-day replication'], 'raw_sha256':{str(q.relative_to(run)):hashlib.sha256(q.read_bytes()).hexdigest() for q in sorted(base.rglob('*')) if q.is_file()}, 'derived_sha256':{q.name:hashlib.sha256(q.read_bytes()).hexdigest() for q in [run/'m3_link_characterization.csv',run/'m3_aggregate_power.csv']}}
(run/'verified_m3_audit.json').write_text(json.dumps(manifest,indent=2)+'\n')
print(json.dumps({'audit':'PASS','experiment':exp,'nodes':nodes,'sent':len(send),'link_trials':len(rec),'rx':manifest['unique_successful_received'],'per_power':per_power,'errors':errors,'monitor_files_parsed':len(noise)},indent=2))
