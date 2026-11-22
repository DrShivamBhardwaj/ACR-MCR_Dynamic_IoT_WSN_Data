#!/usr/bin/env python3
"""Physical M3 UART receipt, no generated or substituted measurements."""
import asyncio,datetime,json,sys,time
from pathlib import Path
exp=sys.argv[1]
output=Path.home()/"acr_opt_m3"/exp
output.mkdir(parents=True,exist_ok=True)
records=[]
async def main():
    started=time.monotonic()
    for i in range(40):
        try:
            read,write=await asyncio.open_connection("m3-14.grenoble.iot-lab.info",20000)
            break
        except OSError:
            if i==39:raise
            await asyncio.sleep(2)
    finished=False
    try:
        with (output/"m3_14.serial.log").open("w") as dest:
            while time.monotonic()-started<470:
                try:line=await asyncio.wait_for(read.readline(),timeout=3)
                except asyncio.TimeoutError:continue
                if not line:break
                raw=line.decode("utf-8","replace").rstrip()
                stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
                dest.write(stamp+"\t"+raw+"\n");dest.flush()
                if "OPT_KERNEL_BOOT" in raw:records.append("BOOT")
                if "OPT_KERNEL_RESULT" in raw:records.append(raw)
                if "OPT_KERNEL_ENERGEST" in raw:records.append(raw)
                if "OPT_KERNEL_DONE" in raw:
                    records.append(raw);finished=True
                    await asyncio.sleep(8)
                    break
    finally:
        write.close();await write.wait_closed()
    summary=dict(experiment=int(exp),source="actual Grenoble m3-14 UART",
      lines=records,complete=finished,
      time_elapsed_s=time.monotonic()-started)
    (output/"capture_summary.json").write_text(json.dumps(summary,indent=2)+"\n")
    print(json.dumps(summary,indent=2),flush=True)
    if not finished:raise SystemExit(2)
asyncio.run(main())
