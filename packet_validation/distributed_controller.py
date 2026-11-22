"""Extended Cooja feedback controller with real over-the-air control frames.

Original Python optimizer source remains unmodified. Packet energy is only a
model, while real Cooja ENERGEST counters are audited independently.
"""
#!/usr/bin/env python3
# Runtime information is derived from Cooja packet events, not the original transaction model.
# Only the sink receives privileged controller-plan injection; other motes use radio control frames.
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
            if not (0<=u<=40 and -1<=v<=40):continue
            attempts=int(item["attempts"]);ok=int(item["status"])==0
            duration=float(item.get("duration_ms",0))
            if attempts<=0:continue
            packet_type=int(item["type"])
            kind="probe" if packet_type==2 else ("control" if packet_type==3 else "data")
            wire_bits=int(item.get("bytes",90))*8
            if packet_type==3 and v!=-1:
                raise ValueError("Control frames must travel via 802.15.4 broadcast")
            if u<40:
                # An accounting estimate, not a current/voltage measurement.
                # Broadcasters transmit to the radio range. Source-to-dest
                # frames use the original synthetic range model.
                estimate_distance=s.cfg.radio_range if v==-1 else float(s.distance[u,v])
                s.debit(u,float(s.radio_tx(estimate_distance,wire_bits))*attempts,kind)
                if 0<=v<40:
                    s.debit(v,wire_bits*s.e_elec*attempts,kind)
                    if ok:s.debit(v,float(s.radio_tx(s.distance[u,v],s.ack_bits)),kind)
                if ok and v!=-1:s.debit(u,s.ack_bits*s.e_elec,kind)
            # Sink-originated control frames have real Cooja MAC/energest
            # evidence but original model does not include sink battery.
            callbacks+=1
            if kind!="probe" or duration<=0 or u>=40 or v<0 or v>=40:continue
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
                     modelled_energy_J=float(sum(s.ledger.values())),
                     modelled_control_energy_J=float(s.ledger["control"]),
                     modelled_probe_energy_J=float(s.ledger["probe"]),
                     modelled_data_energy_J=float(s.ledger["data"]),
                     control_receptions=int(sinks.get("control_applied",0)),
                     control_mac_callbacks=int(sinks.get("control_mac",0)),
                     data_fragment_mac_callbacks=int(sinks.get("fragments",0)))
        self.records.append(summary);self.log("observation",summary)
        if round_id+1>=self.rounds:
            result=dict(closed_loop_packet_feedback=True,
                        radio_control_reception_audited_by_cooja=True,
                        local_radio_mac_provenance=True,
                        distributed_control_packets=True,physical_energy=False,
                        original_payload_fragmentation=True,
                        source_packet_bytes=500,
                        packet_energy_estimated_not_measured=True,
                        sink_control_energy_estimate_excluded=True,
                        controller_source="original acr_mcr_v2.py optimizer",
                        seed=self.seed,scenario=self.scenario,method=self.method,
                        rounds=self.rounds,recorded_epochs=len(self.records),
                        mac_callbacks=sum(r["mac_callbacks"] for r in self.records),
                        probe_callbacks=sum(r["probes_used"] for r in self.records),
                        control_receptions=sum(r["control_receptions"] for r in self.records),
                        control_mac_callbacks=sum(r["control_mac_callbacks"] for r in self.records),
                        fragment_mac_callbacks=sum(r["data_fragment_mac_callbacks"] for r in self.records),
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
    p.add_argument("--rounds",type=int,choices=[4,16,40,160],required=True)
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
