#!/usr/bin/env python3
"""Physical UART capture for reserved Grenoble M3-14,15,18 only."""
import asyncio,datetime,json,sys,time
from pathlib import Path
eid=sys.argv[1]
root=Path.home()/"acr_m3_transport"/eid
root.mkdir(exist_ok=True,parents=True)
NODES=(14,15,18)
begin=time.monotonic()
stats={str(n):dict(lines=0,boot=0,control_applied=0,reassembled=0,mac=0,energest=0) for n in NODES}
done=asyncio.Event()
async def capture(node):
    read,write=await asyncio.open_connection(f"m3-{node}.grenoble.iot-lab.info",20000)
    with (root/f"m3-{node}.log").open("w") as f:
        while time.monotonic()-begin<150:
            try:line=await asyncio.wait_for(read.readline(),timeout=2)
            except asyncio.TimeoutError:
                if done.is_set():break
                continue
            if not line:break
            msg=line.decode("utf-8","replace").rstrip()
            wall=datetime.datetime.now(datetime.timezone.utc).isoformat()
            f.write(f"{wall}\t{msg}\n");f.flush()
            st=stats[str(node)];st["lines"]+=1
            for tag,name in (("M3_TRANSPORT_BOOT","boot"),
                             ("CTRL_APPLIED","control_applied"),
                             ("SINK_REASSEMBLED","reassembled"),
                             ("MAC_TX","mac"),("ENERGEST_RAW","energest")):
                if tag in msg:st[name]+=1
            if node==18 and "DIST_DONE" in msg:
                done.set()
    write.close();await write.wait_closed()
async def main():
    tasks=[asyncio.create_task(capture(n)) for n in NODES]
    try:
        await asyncio.wait_for(done.wait(),timeout=143)
        await asyncio.sleep(5)
    except asyncio.TimeoutError:
        pass
    finally:
        for t in tasks:
            if not t.done():t.cancel()
        results=await asyncio.gather(*tasks,return_exceptions=True)
    errors=[str(x) for x in results if isinstance(x,Exception) and not isinstance(x,asyncio.CancelledError)]
    result=dict(experiment=int(eid),site="Grenoble",physical_boards=list(NODES),
                logical_roles={"14":1,"15":2,"18":41},
                source_code="native M3 fixed cluster/radio transport, NOT original adaptive ACR-MCR",
                sink_reported_done=done.is_set(),per_board=stats,
                errors=errors,capture_duration_s=round(time.monotonic()-begin,3))
    (root/"capture_summary.json").write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result,indent=2),flush=True)
    if errors or not done.is_set():raise SystemExit(2)
asyncio.run(main())
