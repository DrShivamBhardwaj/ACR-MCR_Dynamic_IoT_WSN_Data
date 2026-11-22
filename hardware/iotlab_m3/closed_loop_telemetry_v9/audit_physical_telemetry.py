#!/usr/bin/env python3
"""Observe hardware provenance, actual source probe TX and sink radio receipt.

This cannot establish a closed-loop original ACR-MCR controller.
"""
import argparse,hashlib,json,re
from pathlib import Path
START=re.compile(r'PROBE_TX_EVIDENCE round=(\d+) src=(\d+) to=(\d+) attempts=(\d+) ok=(\d+) duration_ms=(\d+)')
OBS=re.compile(r'SINK_REAL_PROBE_OBS round=(\d+) src=(\d+) to=(\d+) attempts=(\d+) ok=(\d+) duration_ms=(\d+) status=(\d+) via_radio=1')
def audit(root,firmware):
    root=Path(root);manifest=json.loads(Path(firmware).read_text())
    ident={}
    for identifier,role in manifest['physical_roles'].items():
        match=re.fullmatch(r'm3-(\d+)',identifier)
        if not match:raise ValueError('Unregistered physical board name')
        logical=41 if role=='sink41' else (1 if role.startswith('source1') else (2 if role.startswith('source2') else None))
        if logical is None:raise ValueError('Unregistered physical role')
        ident[int(match.group(1))]=logical
    if len(ident)!=3 or set(ident.values())!={1,2,41}:raise ValueError('Physical topology unexpected')
    sinkboard=next(n for n,v in ident.items() if v==41)
    sourceboards={n for n,v in ident.items() if v!=41}
    paths={n:root/f'm3-{n}.log' for n in ident}
    missing=[p.name for p in paths.values() if not p.exists() or not p.stat().st_size]
    if missing:raise RuntimeError('Missing original physical serial: '+repr(missing))
    lines={n:p.read_text(errors='replace') for n,p in paths.items()}
    assert 'DIST_DONE' in lines[sinkboard], 'Sink test did not complete'
    expected={}
    for n in sorted(sourceboards):
        source=ident[n]
        for match in START.finditer(lines[n]):
            round_id,origin,to,attempts,ok,duration=map(int,match.groups())
            if origin!=source or not 0<=round_id<3 or to<1 or to>41:
                raise ValueError('Contradictory source probe event')
            key=(round_id,origin)
            if key in expected:raise ValueError('Duplicate physical source probe observation')
            expected[key]=(to,attempts,ok,duration)
    sink={}
    for match in OBS.finditer(lines[sinkboard]):
        r,source,to,attempts,ok,duration,status=map(int,match.groups())
        key=(r,source)
        if key in sink:raise ValueError('Duplicate matching sink telemetry')
        sink[key]=(to,attempts,ok,duration)
    unmatched={str(k):v for k,v in sink.items() if k not in expected or expected[k]!=v}
    if unmatched:raise ValueError('Sink telemetry did not match any actual source MAC report: '+repr(unmatched))
    energy={n:lines[n].count('ENERGEST_RAW') for n in ident}
    controlled={n:lines[n].count('CTRL_APPLIED') for n in sorted(sourceboards)}
    delivery=[tuple(map(int,m)) for m in re.findall(
       r'SINK_REASSEMBLED round=(\d+) src=(\d+) app_bytes=500 parts=8 checksum=PASS',lines[sinkboard])]
    if len(set(delivery))!=len(delivery):raise ValueError('Duplicate 500B completion')
    records=dict(
        kind='REAL_MAC_PROBE_TELEMETRY_NATIVE_M3',
        verdict='PASS_REAL_PHY_REPORT_PATH' if all(k in {s for _,s in sink} for k in (1,2))
            else ('PARTIAL_TELEMETRY_NETWORK_LOSS' if sink else 'NO_TELEMETRY_RECEIVED'),
        exact_original_link_probe_source_callbacks=len(expected),
        independently_matching_sink_radio_probe_observations=len(sink),
        possible_source_rounds=6,
        matched_physical_source_ids=sorted({source for _,source in sink}),
        source_probe_callback_records=[dict(round=r,logical_source=s,
            destination=x[0],attempts=x[1],mac_success=x[2],
            native_source_elapsed_ms=x[3],
            received_at_sink_radio=(r,s) in sink)
            for (r,s),x in sorted(expected.items())],
        verified_complete_500byte_app_samples=len(delivery),
        actual_source_control_installations=controlled,
        per_board_final_energest_records=energy,
        experiment_not_original_adaptive_acr_mcr=True,
        paper_service_effect_not_measured=True,
        native_source_tick_duration_is_not_cross_node_application_delay=True,
        raw_serial_sha256={str(n):hashlib.sha256(lines[n].encode()).hexdigest() for n in ident},
        firmware_manifest_sha256=hashlib.sha256(Path(firmware).read_bytes()).hexdigest(),
        limitations='Physical radio telemetry return for source MAC probe ACK/attempt/duration, STATIC head routing and 3 rounds only. No predictor, no original ACI integration, no adaptive search or physically synchronized 500-ms data deadline.')
    return records
if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--original-uart',required=True)
    ap.add_argument('--firmware',required=True)
    ap.add_argument('--out',required=True)
    a=ap.parse_args(); result=audit(a.original_uart,a.firmware)
    dest=Path(a.out);dest.parent.mkdir(exist_ok=True,parents=True)
    dest.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    if result['verdict']=='NO_TELEMETRY_RECEIVED':raise SystemExit(2)
