#!/usr/bin/env python3
"""Online feedback bridge: Cooja radio observations update original optimizer.

Central simulator memory injection is used for control (unpriced). This is
Cooja packet-feedback closed loop, NOT distributed MAC-level control validation.
"""
import argparse,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from acr_mcr_v2 import Simulator,Config

class Bridge:
    def __init__(self,seed,scenario,method,rounds,out):
        self.s=Simulator(seed,scenario,method,Config(nodes=40,rounds=rounds))
        self.seed,self.scenario,self.method,self.rounds=seed,scenario,method,rounds
        self.t=-1
        self.out=Path(out);self.out.parent.mkdir(parents=True,exist_ok=True)
        self.file=self.out.open("w");self.records=[]
        self.snap=None

    def log(self,kind,item):
        self.file.write(json.dumps({kind:item})+"\n");self.file.flush()

    def plan(self,t):
        if t!=self.t+1: raise RuntimeError("Controller round order invalid")
        s=self.s
        s.fail_nodes(t)
        _,s.load=s.state(t)
        # No s.environment(): synthetic ACK/duration sampling is DISABLED.
        s.predictions(t)
        p,reason=s.select(t)
        self.snap={name:getattr(s,name).copy() for name in
            ("cost_pred","delay_pred","cost_scale","delay_scale","upper_c","upper_d")}
        self.t=t
        active=s.alive().astype(int).tolist()
        route=[];heads=[]
        for i in range(40):
            c=int(p.assigned[i])
            if c<0 or not active[i]:route.append(0);heads.append(0)
            elif i!=c:route.append(c+1);heads.append(c+1)
            else:
                path=p.paths.get(c,[])
                route.append(path[1]+1 if len(path)>1 else 0);heads.append(c+1)
        options={int(i):int(v)+1 for i,v,q in s.probe_schedule(t) if q==0}
        probes=[options.get(i,0) if active[i] else 0 for i in range(40)]
        packet=dict(round=t,next=route,probes=probes,heads=heads,enabled=active,
                    reason=reason,method=self.method)
        self.log("plan",packet)
        return packet

    def observe(self,round_id,mac,sinks):
        if round_id!=self.t:raise RuntimeError("Observed epoch does not match plan")
        s=self.s
        scores=[];covered=[];probe_count=0;callbacks=0
        for item in mac:
            if int(item["round"])!=round_id:continue
            u=int(item["sender"])-1;v=int(item["to"])-1
            if not (0<=u<40 and 0<=v<=40):continue
            attempts=int(item["attempts"]);ok=int(item["status"])==0
            duration=float(item.get("duration_ms",0))
            if attempts<=0:continue
            kind="probe" if int(item["type"])==2 else "data"
            # The energy debit is a radio-model estimate driven by actual
            # packet attempts, not a physical energy measurement.
            s.debit(u,float(s.radio_tx(s.distance[u,v],78*8))*attempts,kind)
            if v<40:
                s.debit(v,78*8*s.e_elec*attempts,kind)
                if ok:s.debit(v,float(s.radio_tx(s.distance[u,v],s.ack_bits)),kind)
            if ok:s.debit(u,s.ack_bits*s.e_elec,kind)
            callbacks+=1
            if kind!="probe" or duration<=0:continue
            cost=min(5.,float(attempts+int(not ok)))
            c_hat=float(self.snap["cost_pred"][u,v])
            d_hat=float(self.snap["delay_pred"][u,v])
            c_scale=float(self.snap["cost_scale"][u,v])
            d_scale=float(self.snap["delay_scale"][u,v])
            scores.append([(cost-c_hat)/max(.35,c_scale),
                           (duration-d_hat)/max(4.,d_scale)])
            covered.append([cost<=float(self.snap["upper_c"][u,v]),
                            duration<=float(self.snap["upper_d"][u,v])])
            s.beta_a[u,v]=.9*s.beta_a[u,v]+int(ok)
            s.beta_b[u,v]=.9*s.beta_b[u,v]+attempts-int(ok)
            s.frame_hat[u,v]=.8*s.frame_hat[u,v]+.2*duration/attempts
            probe_count+=1
        if scores:s.cal.update(np.asarray(scores,float),np.asarray(covered,bool),round_id)
        summary=dict(round=round_id,mac_callbacks=callbacks,probes_used=probe_count,
                     sink_unique=int(sinks.get("unique",0)),
                     timely500=int(sinks.get("timely",0)),
                     searches=s.searches,alpha_cost=float(s.cal.alpha[0]),
                     modelled_energy_J=float(sum(s.ledger.values())))
        self.records.append(summary);self.log("observation",summary)
        if round_id+1>=self.rounds:
            result=dict(closed_loop_packet_feedback=True,
                        distributed_control_packets=False,physical_energy=False,
                        original_payload_fragmentation=False,
                        controller_source="original acr_mcr_v2.py optimizer",
                        seed=self.seed,scenario=self.scenario,method=self.method,
                        rounds=self.rounds,recorded_epochs=len(self.records),
                        mac_callbacks=sum(r["mac_callbacks"] for r in self.records),
                        probe_callbacks=sum(r["probes_used"] for r in self.records),
                        controller_searches=s.searches,
                        controller_fitness_evaluations=s.fitness_calls)
            self.out.with_suffix(".summary.json").write_text(json.dumps(result,indent=2)+"\n")
            self.file.flush()
            return {"done":True,"summary":result}
        return self.plan(round_id+1)

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--scenario",choices=["S1","S5"],required=True)
    p.add_argument("--method",choices=["POINT-EA","ACR-MCR"],required=True)
    p.add_argument("--rounds",type=int,choices=[16,40,160],required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    bridge=Bridge(a.seed,a.scenario,a.method,a.rounds,a.out)
    for line in sys.stdin:
        try:
            req=json.loads(line)
            if req.get("cmd")=="init":result=bridge.plan(0)
            elif req.get("cmd")=="observe":
                result=bridge.observe(int(req["round"]),req["mac"],req["sinks"])
            else:raise ValueError("Unknown bridge command")
            print(json.dumps(result),flush=True)
            if result.get("done"):break
        except Exception as e:
            print(json.dumps({"error":type(e).__name__+": "+str(e)}),flush=True)
            print(repr(e),file=sys.stderr,flush=True)
            raise
if __name__=="__main__":main()
