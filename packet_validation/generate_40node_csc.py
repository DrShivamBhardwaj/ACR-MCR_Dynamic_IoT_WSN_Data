#!/usr/bin/env python3
"""Build a 41-mote Cooja scenario for a 40-sensor open-loop decision replay."""
import argparse
import copy
import json
from pathlib import Path
import xml.etree.ElementTree as ET

SCRIPT=r'''
TIMEOUT(TIMEOUT_MS);
var requested=0,delivered=0,probeTx=0,macCount=0,failedMac=0;
var seen={}, startTimes={}, timely=0;
while(true) {
  YIELD();
  if(msg.contains("DATA_DEMAND")) {
    requested++;
    var startKey=String(msg).match(/round=(\d+) src=(\d+)/);
    if(startKey) startTimes[startKey[1]+":"+startKey[2]]=sim.getSimulationTime();
    log.log("DEMAND_TRACE " + msg + "\n");
  }
  if(msg.contains("SINK_RECV")) {
    var m=String(msg).match(/round=(\d+) src=(\d+)/);
    if(m) {
      var key=m[1]+":"+m[2];
      if(!seen[key]) {
        delivered++; seen[key]=true;
        var delay=startTimes[key]===undefined?-1:(sim.getSimulationTime()-startTimes[key])/1000.0;
        if(delay>=0 && delay<=500) timely++;
        log.log("LATENCY_TRACE mode=METHOD seed=SEED key="+key+" ms="+delay+"\n");
      }
    }
    log.log("SINK_TRACE " + msg + "\n");
  }
  if(msg.contains("MAC_TX")) {
    macCount++;
    if(msg.contains("type=2")) probeTx++;
    if(!msg.contains("status=0 ")) failedMac++;
    log.log("MAC_TRACE " + msg + "\n");
  }
  if(msg.contains("NODE_DISABLE") || msg.contains("DROP_QUEUE")) {
    log.log("CONSTRAINT_TRACE " + msg + "\n");
  }
  if(id==1 && msg.contains("REPLAY_DONE")) {
    log.log("REPLAY_SUMMARY mode=METHOD seed=SEED scenario=SCENARIO rounds=ROUNDS requested=" +
        requested + " unique_sink=" + delivered + " timely500=" + timely + " mac_callbacks=" + macCount +
        " failures=" + failedMac + " probe_callbacks=" + probeTx + "\n");
    log.log("DONE_TRACE " + msg + "\n");
    if(requested >= 20 && macCount >= 20) log.testOK();
    else log.testFailed();
  }
}
'''

def build(args):
    tree=ET.parse(args.template)
    root=tree.getroot()
    sim=root.find("simulation")
    sim.find("title").text=f"ACR 40-node open-loop {args.method} S{args.scenario} seed{args.seed}"
    sim.find("randomseed").text=str(args.seed)
    medium=sim.find("radiomedium")
    medium.find("transmitting_range").text=str(args.radio_range)
    medium.find("interference_range").text=str(args.radio_range*1.20)
    medium.find("success_ratio_tx").text="1.0"
    medium.find("success_ratio_rx").text=str(args.rx_success)
    motetype=sim.find("motetype")
    motetype.find("description").text="40-node route/telemetry replay of ACR original Python decisions"
    motetype.find("source").text="[CONTIKI_DIR]/examples/acr_mcr_40/acr_40_replay.c"
    motetype.find("commands").text="$(MAKE) TARGET=cooja clean\n$(MAKE) acr_40_replay.cooja TARGET=cooja"
    src_motes=motetype.findall("mote")
    if not src_motes: raise ValueError("Cooja template has no mote to clone")
    for m in src_motes: motetype.remove(m)
    positions=json.loads(Path(args.positions).read_text())
    xy=positions["sensors"]+[positions["sink"]]
    if len(xy)!=41: raise ValueError("40 sensors plus sink must be defined")
    for moteid,(x,y) in enumerate(xy,1):
        m=copy.deepcopy(src_motes[0])
        found_pos=found_id=False
        for interface in m.findall("interface_config"):
            label=interface.text or ""
            if "Position" in label:
                pt=interface.find("pos")
                if pt is not None:
                    pt.set("x",str(float(x)));pt.set("y",str(float(y)))
                    found_pos=True
            if "MoteID" in label:
                ix=interface.find("id")
                if ix is not None:
                    ix.text=str(moteid)
                    found_id=True
        if not (found_pos and found_id):
            raise ValueError(f"Failed setting position/ID for node {moteid}")
        motetype.append(m)
    plugins=root.findall("plugin")
    script_nodes=[p.find("plugin_config/script") for p in plugins if "ScriptRunner" in (p.text or "")]
    script_nodes=[x for x in script_nodes if x is not None]
    if len(script_nodes)!=1: raise ValueError("ScriptRunner plugin not found")
    expiry=int((args.rounds*5+80)*1000)
    script_nodes[0].text=(SCRIPT.replace("TIMEOUT_MS",str(expiry))
      .replace("METHOD",str(1 if args.method=="ACR-MCR" else 0))
      .replace("SEED",str(args.seed)).replace("SCENARIO",args.scenario)
      .replace("ROUNDS",str(args.rounds)))
    ET.indent(tree,space="  ")
    dest=Path(args.out);dest.parent.mkdir(parents=True,exist_ok=True)
    tree.write(dest,encoding="unicode",xml_declaration=True)
    print(f"SCENARIO_READY nodes=41 mode={args.method} seed={args.seed} rounds={args.rounds} path={dest}")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--template",required=True)
    p.add_argument("--positions",required=True)
    p.add_argument("--method",choices=["POINT-EA","ACR-MCR"],required=True)
    p.add_argument("--scenario",choices=["S1","S5"],required=True)
    p.add_argument("--seed",type=int,required=True)
    p.add_argument("--rx-success",type=float,default=0.94)
    p.add_argument("--radio-range",type=float,default=78.0)
    p.add_argument("--rounds",type=int,choices=[16,40,160],required=True)
    p.add_argument("--out",required=True)
    a=p.parse_args()
    build(a)
