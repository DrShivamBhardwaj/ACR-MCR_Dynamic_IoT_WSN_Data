#!/usr/bin/env python3
"""Independent evidence gate for physical feedback, not a controller update."""
import hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
a=root/'hardware/iotlab_m3/closed_loop_telemetry_v9/evidence/459639/strict_radio_telemetry_audit.json'
s=json.loads(a.read_text()); obs=s['source_probe_callback_records']
assert s['verdict']=='PASS_REAL_PHY_REPORT_PATH'
assert len(obs)==6 and s['independently_matching_sink_radio_probe_observations']==6
assert all(x['received_at_sink_radio'] and x['destination']==41 for x in obs)
assert len({(x['round'],x['logical_source'],x['destination']) for x in obs})==6
assert sorted({x['logical_source'] for x in obs})==[1,2]
# The original transaction() uses duration=now-begin in ms, and cost=attempts+int(not success).
# Native callback durations here are local tick elapsed times, NOT proven to have the
# same semantic definition as original full transaction durations.
rows=[dict(round=x['round'],u=x['logical_source']-1,v=40,attempts=x['attempts'],success=x['mac_success'],native_elapsed_ms=x['native_source_elapsed_ms'],cost_candidate=x['attempts']+int(not x['mac_success']),received_at_sink=True) for x in obs]
out=dict(status='PASS_TELEMETRY_INPUT_GATE_ONLY',source_file=str(a.relative_to(root)),source_sha256=hashlib.sha256(a.read_bytes()).hexdigest(),experiment=459639,observations=rows,original_python_edge_index='logical source 1 -> 0, 2 -> 1; sink 41 -> 40',blocked_for_original_controller=['MAC callback native elapsed may differ from original transaction duration','no source-to-sink time synchronization for full transaction duration','physical link observations cover only 2 of 40 sources and direct-to-sink edges','original conformal residual requires frozen pre-observation predictor state, scales and q values','no post-round C/Python parity or next-head-search physical plan yet'],adaptive_closed_loop_pass=False)
p=root/'research_reconstruction/V9_PHYSICAL_FEEDBACK_INPUT_GATE_459639.json';p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(dict(status=out['status'],source_sha256=out['source_sha256'],rows=len(rows),output=str(p)),indent=2))
