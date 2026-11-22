#!/usr/bin/env python3
"""Forty-source plus one sink IoT-LAB physical UART capture, no synthetic rows."""
import asyncio,datetime,json,sys,time
from pathlib import Path
eid=sys.argv[1]
manifest=json.loads((Path.home()/"acr_m3_transport_41"/"physical_layout.json").read_text())
roles={int(v["board"]):int(k) for k,v in manifest["nodes"].items()}
roles[int(manifest["sink_physical_board"])]=41
assert len(roles)==41
out=Path.home()/"acr_m3_transport_41"/eid
out.mkdir(parents=True,exist_ok=False)
begin=time.monotonic()
done=asyncio.Event()
counts={str(board):dict(logical_id=role,raw_lines=0,control_received=0,
                      mac_callbacks=0,reassembled_500B=0,energy_snapshots=0,
                      boot_records=0) for board,role in roles.items()}
errors=[]
async def capture(board,logical):
    st=counts[str(board)]
    try:
        # Connect while the reservation is still launching. Some M3 UART
        # sockets appear only when individual firmware flashes complete.
        for attempt in range(60):
            try:
                read,write=await asyncio.open_connection(
                    f"m3-{board}.grenoble.iot-lab.info",20000)
                break
            except OSError:
                if attempt==59:raise
                await asyncio.sleep(1.5)
        with (out/f"m3-{board}_logical-{logical}.serial.log").open("w") as f:
            while time.monotonic()-begin<285:
                try:line=await asyncio.wait_for(read.readline(),timeout=2.5)
                except asyncio.TimeoutError:
                    if done.is_set():break
                    continue
                if not line:break
                msg=line.decode("utf-8","replace").rstrip()
                f.write(datetime.datetime.now(datetime.timezone.utc).isoformat()+"\t"+msg+"\n")
                f.flush()
                st["raw_lines"]+=1
                for label,name in (
                  ("CTRL_APPLIED","control_received"),
                  ("MAC_TX ","mac_callbacks"),
                  ("SINK_REASSEMBLED","reassembled_500B"),
                  ("ENERGEST_RAW","energy_snapshots"),
                  ("M3_TRANSPORT_BOOT","boot_records")):
                    if label in msg:st[name]+=1
                if logical==41 and "DIST_DONE" in msg:done.set()
        write.close();await write.wait_closed()
    except Exception as exc:
        errors.append(dict(board=board,logical=logical,error=repr(exc)))
async def main():
    tasks=[asyncio.create_task(capture(board,logical))
           for board,logical in sorted(roles.items())]
    try:
        await asyncio.wait_for(done.wait(),timeout=260)
        await asyncio.sleep(20)
    except asyncio.TimeoutError:
        pass
    for t in tasks:
        if not t.done():t.cancel()
    await asyncio.gather(*tasks,return_exceptions=True)
    report=dict(
      experiment=int(eid),site="Grenoble",requested_sources=40,
      requested_sink_nodes=1,requested_rounds=3,
      sink_reported_experiment_finished=done.is_set(),
      captured_serial_nodes=sum(c["raw_lines"]>0 for c in counts.values()),
      control_receptions=sum(c["control_received"] for c in counts.values()),
      full_500B_sink_reassemblies=counts[str(manifest["sink_physical_board"])]["reassembled_500B"],
      physical_serial_records=counts,errors=errors,
      scientific_limit="STATIC sink-generated four-cluster route map. Adaptive ACR-MCR does NOT execute on M3. No synchronized 500ms latency claim.",
      capture_duration_s=round(time.monotonic()-begin,3))
    (out/"capture_summary.json").write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps({k:v for k,v in report.items() if k!="physical_serial_records"},indent=2),flush=True)
    if errors or not done.is_set():raise SystemExit(2)
asyncio.run(main())
