"""Scientific invariants; does not assert favourable algorithm outcomes."""
import json
import math
from dataclasses import replace
from pathlib import Path
import numpy as np
from acr_mcr_v2 import Config, Simulator, Calibrator, empirical_cvar, keyed_uniform

def main():
    checks = {}
    cfg = Config(nodes=12,rounds=25,warmup=5,population=4,generations=1)
    s = Simulator(9000,'S5','ACR-MCR',cfg,True)
    initial = s.energy.sum()
    s.fail_nodes(20)
    assert s.disabled.sum() == 2 and s.energy.sum() == initial and sum(s.ledger.values()) == 0
    checks['external_failure_preserves_energy_ledger'] = True
    s = Simulator(9001,'S1','POINT-EA',cfg)
    s.environment(6); s.predictions(6)
    p0 = s.cost_pred.copy()
    s.env_p[:] = .00001; s.env_frame[:] = 1000
    s.predictions(6)
    np.testing.assert_array_equal(p0,s.cost_pred)
    checks['forecast_does_not_read_latent_channel'] = True
    env_a = Simulator(9001,'S1','POINT-EA',cfg)
    env_b = Simulator(9001,'S1','ACR-MCR',cfg)
    for t in (0,6,18):
        env_a.environment(t); env_b.environment(t)
        assert env_a.env_fingerprint == env_b.env_fingerprint
        assert env_a.probe_schedule(t) == env_b.probe_schedule(t)
    a = keyed_uniform(1,2,3,4,5,6,7,8)
    for x in range(100): keyed_uniform(x,3,4,5,6,7,8,9)
    assert a == keyed_uniform(1,2,3,4,5,6,7,8)
    checks['indexed_fields_and_probe_schedule_are_policy_independent'] = True
    s = Simulator(9002,'S0','ACR-MCR',cfg)
    s.heads = np.array([0,1]); s.last_search=5
    s.cal.recent_coverage=[np.array([0.,0.])]*3
    assert s.trigger(7) is None and s.trigger(8) == 'coverage'
    s.cal.recent_coverage=[np.ones(2)]*3
    assert s.trigger(8) is None and s.trigger(15) == 'periodic'
    checks['coverage_trigger_reachable_between_minimum_and_maximum_gap'] = True
    assert abs(empirical_cvar(np.arange(64),.9) - (sum(range(58,64))+.4*57)/6.4)<1e-12
    assert empirical_cvar(np.ones(64),.9)==1
    checks['fractional_empirical_expected_shortfall'] = True
    cal = Calibrator(cfg,'adaptive')
    cal.q[:] = 0
    before = cal.q.copy()
    scores=np.array([[2.,3.],[1.,2.]])
    issued = scores<=before
    cal.update(scores,issued,6)
    assert not issued.any() and cal.q.min()>0 and (cal.alpha<cfg.target_alpha).all()
    checks['coverage_scored_against_pre_update_bounds'] = True
    frozen=Calibrator(cfg,'frozen')
    frozen.update(scores,issued,0); old=frozen.q.copy()
    frozen.update(scores*100,issued,6)
    np.testing.assert_array_equal(frozen.q,old)
    checks['frozen_calibrator_remains_frozen'] = True
    s=Simulator(9003,'S0','POINT-EA',cfg,True)
    s.environment(0);s.predictions(0)
    plan=s.make_plan([0,1])
    for i,c in enumerate(plan.assigned):
        if c>=0 and i!=c: assert s.distance[i,c]<=cfg.radio_range
    for path in plan.paths.values():
        assert len(path)==len(set(path))
        assert all(s.distance[u,v]<=cfg.radio_range for u,v in zip(path[:-1],path[1:]))
    checks['range_applies_to_members_backbone_and_loop_free_paths'] = True
    s=Simulator(9004,'S0','POINT-EA',replace(cfg,radio_range=1.0),True)
    result=s.run()
    assert result['PDR']==0 and result['timely_ratio']==0 and result['service_violation_rate']==1
    assert all(r['demand']==12 for r in s.rows)
    checks['unreachable_demand_is_not_removed'] = True
    s=Simulator(9005,'S4','ACR-MCR',cfg,True)
    result=s.run()
    np.testing.assert_allclose(s.energy0.sum()-s.energy.sum(),sum(s.ledger.values()),atol=1e-10)
    assert all(s.ledger[k]>0 for k in s.ledger)
    assert all(x['distance_m']<=cfg.radio_range for x in s.link_logs)
    assert all(x['cost']>=1 and x['cost']<=5 for x in s.link_logs)
    checks['complete_radio_ledger_and_range_in_executed_transactions'] = True
    # Half-duplex queueing is included in packet completion timestamps.
    s=Simulator(9006,'S0','POINT-EA',cfg)
    s.environment(0);s.predictions(0);s.env_p[:]=1
    u,v=next((i,int(j)) for i in range(s.n) for j in np.where(s.feasible[i,:s.n])[0])
    busy=np.zeros(s.n)
    ok,t1,_=s.transaction(0,u,v,u,0,72,0,busy)
    ok2,t2,_=s.transaction(0,u,v,u,1,72,0,busy)
    assert ok and ok2 and t2>t1 and abs(t2-2*t1)<1e-8
    checks['node_queueing_contributes_to_delivery_timestamp'] = True
    a=Simulator(9007,'S2','ACR-MCR',cfg)
    b=Simulator(9007,'S2','ACR-MCR',cfg)
    ra,rb=a.run(),b.run()
    for key in ra:
        if 'seconds' not in key:
            assert ra[key]==rb[key] or (isinstance(ra[key],float) and math.isnan(ra[key]) and math.isnan(rb[key])),key
    assert a.rows==b.rows
    checks['deterministic_replay_except_wall_time'] = True
    # Warm-up is matched even for the full method.
    a=Simulator(9008,'S2','ACI-EVENT',cfg)
    b=Simulator(9008,'S2','ACR-MCR',cfg)
    a.run(); b.run()
    assert a.rows[:cfg.warmup]==b.rows[:cfg.warmup]
    checks['tail_ablation_matches_before_tail_activation'] = True
    out=Path('verification.json');out.write_text(json.dumps(checks,indent=2)+'\n')
    print(json.dumps(checks,indent=2))

if __name__=='__main__': main()
