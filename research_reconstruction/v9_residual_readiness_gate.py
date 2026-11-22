#!/usr/bin/env python3
"""Fail-closed readiness audit for feeding M3 observations to original controller.
This audit does not update the original controller or infer missing predictor state.
"""
import hashlib,json,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
source=root/'research_reconstruction/V9_PHYSICAL_FEEDBACK_INPUT_GATE_459639.json'
d=json.loads(source.read_text())
assert d['status']=='PASS_TELEMETRY_INPUT_GATE_ONLY' and d['experiment']==459639
assert len(d['observations'])==6
assert all(x['received_at_sink'] and x['v']==40 and x['u'] in (0,1) for x in d['observations'])
assert len({(x['round'],x['u'],x['v']) for x in d['observations']})==6
# A successful MAC callback is not a measured end-to-end transaction latency.
# The original controller cannot compute a conformal residual without its
# pre-observation prediction, scale and calibration quantile for the same edge.
required={'pre_observation_predictor_snapshot':'MISSING','per_edge_original_scale':'MISSING','pre_observation_conformal_quantile':'MISSING','native_to_original_duration_semantics':'UNVALIDATED','C_Python_post_round_state_parity':'NOT_RUN','physical_next_plan_actuation':'NOT_RUN'}
assert all(x in ('MISSING','UNVALIDATED','NOT_RUN') for x in required.values())
out={'verdict':'BLOCKED_NO_VALIDATED_RESIDUAL_UPDATE','experiment':459639,'physical_probe_records':6,'physical_edges_observed':2,'source_input_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'required_gates':required,'controller_state_changed':False,'physical_closed_loop_pass':False,'note':'Preserves successful physical probe stage; no inferred residual, calibrated duration or physical deadline.'}
target=root/'research_reconstruction/V9_RESIDUAL_READINESS_459639.json';target.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
