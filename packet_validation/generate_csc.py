#!/usr/bin/env python3
"""Create reproducible Contiki-NG Cooja configurations from a pinned template."""
import argparse
import copy
from pathlib import Path
import xml.etree.ElementTree as ET

SCRIPT = r'''
TIMEOUT(145000);
var delivered = 0, timely = 0, probed = 0, dataTx = 0, relayed = 0, searches = 0;
var startAt = {};
while(true) {
  YIELD();
  if (id == 4 && msg.contains("DATA_START")) {
    var txMatch = String(msg).match(/round=(\d+)/);
    if (txMatch) startAt[txMatch[1]] = sim.getSimulationTime();
  }
  if (id == 1 && msg.contains("SINK_DATA")) {
    delivered++;
    var rxMatch = String(msg).match(/round=(\d+)/);
    var ms = -1;
    if (rxMatch && startAt[rxMatch[1]] !== undefined) {
      ms = (sim.getSimulationTime() - startAt[rxMatch[1]]) / 1000.0;
      if (ms >= 0 && ms <= 500) timely++;
    }
    log.log("DATA_TRACE " + msg + " host_elapsed_ms=" + ms + "\n");
  }
  if (id == 4 && msg.contains("PROBE_RESULT")) {
    probed++;
    log.log("PROBE_TRACE " + msg + "\n");
  }
  if (id == 4 && msg.contains("DATA_TX")) {
    dataTx++;
    log.log("SOURCE_TRACE " + msg + "\n");
  }
  if (id == 4 && msg.contains("HEAD_CHOICE")) {
    searches++;
    log.log("CONTROL_TRACE " + msg + "\n");
  }
  if ((id == 2 || id == 3) && msg.contains("RELAY_TX")) {
    relayed++;
    log.log("RELAY_TRACE " + msg + "\n");
  }
  if (id == 4 && msg.contains("DONE")) {
    log.log("VALIDATION_SUMMARY mode=MODE seed=SEED delivered=" +
            delivered + " timely=" + timely + " probe_callbacks=" + probed +
            " data_callbacks=" + dataTx + " relay_callbacks=" + relayed +
            " head_searches=" + searches + "\n");
    log.log("SENDER_DONE " + msg + "\n");
    if (probed >= 20 && delivered >= 3 && relayed >= 3) {
      log.testOK();
    } else {
      log.testFailed();
    }
  }
}
'''

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--template",required=True)
    ap.add_argument("--mode",type=int,choices=[0,1],required=True)
    ap.add_argument("--seed",type=int,required=True)
    ap.add_argument("--rx-success",type=float,default=0.92)
    ap.add_argument("--out",required=True)
    args=ap.parse_args()
    if not 0.55 <= args.rx_success <= 1.0:
        ap.error("Receiver success must be 0.55..1.00")
    tree=ET.parse(args.template)
    root=tree.getroot()
    sim=root.find("simulation")
    sim.find("title").text=f"ACR packet mechanism mode={args.mode} seed={args.seed}"
    sim.find("randomseed").text=str(args.seed)
    radio=sim.find("radiomedium")
    radio.find("transmitting_range").text="54.0"
    radio.find("interference_range").text="85.0"
    radio.find("success_ratio_tx").text="1.0"
    radio.find("success_ratio_rx").text=str(args.rx_success)
    mt=sim.find("motetype")
    mt.find("description").text="ACR packet-level mechanism (4 nodes)"
    mt.find("source").text="[CONTIKI_DIR]/examples/acr_mcr_packet/acr_packet.c"
    mt.find("commands").text=(
        "$(MAKE) TARGET=cooja clean\n"
        f"$(MAKE) acr_packet.cooja TARGET=cooja MODE={args.mode}"
    )
    motes=mt.findall("mote")
    if len(motes)<3:
        raise RuntimeError("Unexpected Contiki-NG template motes")
    # 1 sink, 2/3 candidate cluster relays, 4 sensor.
    points={1:(48.0,48.0),2:(48.0,0.0),3:(0.0,48.0),4:(0.0,0.0)}
    for mote in list(motes): mt.remove(mote)
    for id,(x,y) in points.items():
        mote=copy.deepcopy(motes[0])
        for interface in mote.findall("interface_config"):
            if interface.text and "Position" in interface.text:
                pos=interface.find("pos")
                if pos is not None: pos.set("x",str(x)); pos.set("y",str(y))
            if interface.text and "MoteID" in interface.text:
                ix=interface.find("id")
                if ix is not None: ix.text=str(id)
        mt.append(mote)
    plugins=root.findall("plugin")
    scripts=[p.find("plugin_config/script") for p in plugins if "ScriptRunner" in (p.text or "")]
    scripts=[s for s in scripts if s is not None]
    if len(scripts)!=1: raise RuntimeError("Template script plugin not found")
    scripts[0].text=SCRIPT.replace("MODE",str(args.mode)).replace("SEED",str(args.seed))
    ET.indent(tree,space="  ")
    dest=Path(args.out)
    dest.parent.mkdir(parents=True,exist_ok=True)
    tree.write(dest,encoding="unicode",xml_declaration=True)
    print(f"Generated {dest}, source mode={args.mode}, seed={args.seed}")
if __name__=="__main__": main()
