#!/usr/bin/env python3
"""Fail-closed 41-M3 UART capture with reservation and startup integrity checks."""
import asyncio,datetime,json,re,sys,time
from pathlib import Path
EID=int(sys.argv[1]); METHOD=sys.argv[2]; RESERVED=datetime.datetime.fromisoformat(sys.argv[3].replace('Z','+00:00'))
assert METHOD in ('POINT-EA','ACR-MCR') and RESERVED.tzinfo
EXPECTED_METHOD=0 if METHOD=='POINT-EA' else 1
MAC_MINUS_SITE_SECONDS=float(sys.argv[4])
if not 120 < MAC_MINUS_SITE_SECONDS < 240:
 raise ValueError("The observed clock skew must be measured, not assumed")
layout_file=Path.home()/'acr_m3_transport_41'/'registered_v6_seed9402_layout_b3.json'
import hashlib
if hashlib.sha256(layout_file.read_bytes()).hexdigest()!='2ed35598b47951c79af4588cd02004cdd974b609105c11fa7e1d78f3da365687':
 raise ValueError('FAIL_CLOSED_CAPTURE_MISMATCH: the exact registered V6 physical layout changed')
layout=json.loads(layout_file.read_text())
roles={int(v['board']):int(k) for k,v in layout['nodes'].items()}
roles[int(layout['sink_physical_board'])]=41
assert len(roles)==41 and len(set(roles.values()))==41
out=Path.home()/'acr_m3_transport_41'/str(EID);out.mkdir(parents=True,exist_ok=False)
start=time.monotonic();done=asyncio.Event();errors=[];counts={}
for board,logical in roles.items():
 counts[str(board)]=dict(logical_id=logical,raw_lines=0,boot_records=0,control_received=0,mac_callbacks=0,reassembled_500B=0,energy_snapshots=0,first_timestamp_utc=None,last_timestamp_utc=None,connected_utc=None,disconnected_utc=None,first_boot_utc=None,boot_id_verified=False,boot_method_verified=False,pre_reservation_lines=0,post_done_lines=0)
async def capture(board,logical):
 st=counts[str(board)];reader=writer=None
 try:
  for attempt in range(90):
   try:
    reader,writer=await asyncio.open_connection(f'm3-{board}.grenoble.iot-lab.info',20000)
    st['connected_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();break
   except OSError:
    if attempt==89:raise
    await asyncio.sleep(1)
  with (out/f'm3-{board}_logical-{logical}.serial.log').open('w') as f:
   while time.monotonic()-start<300:
    try:line=await asyncio.wait_for(reader.readline(),timeout=2)
    except asyncio.TimeoutError:
     if done.is_set() and time.monotonic()-done_at[0]>30:break
     continue
    if not line:break
    now=datetime.datetime.now(datetime.timezone.utc);msg=line.decode('utf-8','replace').rstrip()
    f.write(now.isoformat()+'\t'+msg+'\n');f.flush()
    st['raw_lines']+=1;st['first_timestamp_utc']=st['first_timestamp_utc'] or now.isoformat();st['last_timestamp_utc']=now.isoformat()
    # Compare with measured site-to-host offset and 5s network uncertainty.
    if now+datetime.timedelta(seconds=MAC_MINUS_SITE_SECONDS)<RESERVED-datetime.timedelta(seconds=5):
     st['pre_reservation_lines']+=1
    if done.is_set():st['post_done_lines']+=1
    if 'M3_TRANSPORT_BOOT ' in msg:
     st['boot_records']+=1;st['first_boot_utc']=st['first_boot_utc'] or now.isoformat()
     match=re.search(r'\bid=(\d+)\b',msg);method=re.search(r'\bmethod=(\d+)\b',msg)
     st['boot_id_verified']=bool(match and int(match.group(1))==logical)
     st['boot_method_verified']=bool(method and int(method.group(1))==(EXPECTED_METHOD if logical==41 else 0))
    for label,key in [('CTRL_APPLIED','control_received'),('MAC_TX ','mac_callbacks'),('SINK_REASSEMBLED','reassembled_500B'),('ENERGEST_RAW','energy_snapshots')]:
     if label in msg:st[key]+=1
    if logical==41 and 'DIST_DONE' in msg and not done.is_set():done_at[0]=time.monotonic();done.set()
 except Exception as exc:errors.append(dict(board=board,logical=logical,error=repr(exc)))
 finally:
  st['disconnected_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
  if writer:
   writer.close()
   try:await writer.wait_closed()
   except OSError:pass
async def main():
 tasks=[asyncio.create_task(capture(b,l)) for b,l in sorted(roles.items())]
 try:await asyncio.wait_for(done.wait(),timeout=265)
 except asyncio.TimeoutError:pass
 if done.is_set():await asyncio.sleep(30)
 for t in tasks:
  if not t.done():t.cancel()
 await asyncio.gather(*tasks,return_exceptions=True)
 missing=[dict(board=int(b),logical_id=v['logical_id']) for b,v in counts.items() if not v['raw_lines']]
 missing_boot=[dict(board=int(b),logical_id=v['logical_id']) for b,v in counts.items() if not v['boot_records']]
 bad_boot=[dict(board=int(b),logical_id=v['logical_id']) for b,v in counts.items() if v['boot_records'] and not (v['boot_id_verified'] and v['boot_method_verified'])]
 stale=[dict(board=int(b),logical_id=v['logical_id'],count=v['pre_reservation_lines']) for b,v in counts.items() if v['pre_reservation_lines']]
 failures=[]
 if errors:failures.append('UART_CONNECTION_ERRORS')
 if missing:failures.append('MISSING_NODE_UART')
 warnings=[]
 if missing_boot:warnings.append('UNCAPTURED_EARLY_BOOT_MESSAGES')
 # Sink BOOT CL_METHOD is a transport build marker and may be 0
 # even for risk=1: method-specific ONBOARD_OPT_READY is authoritative.
 node_bad=[x for x in bad_boot if x['logical_id']!=41]
 if node_bad:failures.append('SOURCE_BOOT_ADDRESS_MISMATCH')
 if len(bad_boot)>len(node_bad):warnings.append('SINK_BOOT_METHOD_FLAG_NOT_ACTUAL_KERNEL')
 if stale:failures.append('PRE_RESERVATION_UART_ACTIVITY')
 if not done.is_set():failures.append('MISSING_SINK_DONE')
 sink_board=int(layout['sink_physical_board'])
 sink_log=out/f'm3-{sink_board}_logical-41.serial.log'
 sink_text=sink_log.read_text(errors='replace') if sink_log.exists() else ''
 expected_fixture=f'{METHOD}_9402_S5_r20'
 actual_ready=re.findall(r'ONBOARD_OPT_READY fixture=(\S+) risk=(\d+)',sink_text)
 if len(actual_ready)!=1 or actual_ready[0]!=(expected_fixture,str(EXPECTED_METHOD)):
  failures.append('SINK_FROZEN_ORIGINAL_METHOD_SPECIFIC_KERNEL_NOT_PROVEN')
 summary=dict(experiment=EID,method=METHOD,reservation_utc=RESERVED.isoformat(),site='Grenoble',requested_sources=40,requested_sink_nodes=1,requested_rounds=3,sink_reported_experiment_finished=done.is_set(),captured_serial_nodes=41-len(missing),control_receptions=sum(v['control_received'] for v in counts.values()),full_500B_sink_reassemblies=counts[str(layout['sink_physical_board'])]['reassembled_500B'],physical_serial_records=counts,errors=errors,missing_uart=missing,missing_boot=missing_boot,bad_boot=bad_boot,stale_uart=stale,failures=failures,warnings=warnings,
site_to_mac_clock_offset_seconds=MAC_MINUS_SITE_SECONDS,
expected_original_kernel_fixture=expected_fixture,
observed_sink_kernel_markers=actual_ready,
missing_boot_is_warning_not_firmware_proof=True,
scientific_validation_pass=not failures,scientific_limit='STATIC frozen controller; NOT adaptive closed-loop ACR-MCR. Source firmware method=0 for both arms; sink method identifies arm.',capture_duration_s=round(time.monotonic()-start,3))
 (out/'capture_summary.json').write_text(json.dumps(summary,indent=2)+'\n')
 print(json.dumps({k:v for k,v in summary.items() if k!='physical_serial_records'},indent=2),flush=True)
 if failures:raise SystemExit(2)
done_at=[0.0]
asyncio.run(main())
