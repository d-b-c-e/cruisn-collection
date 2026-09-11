"""Hand-calculated worker schedules and corrupt-journal rejection; no devices."""
import csv
import json
from pathlib import Path
import struct
import subprocess
import sys
import tempfile

FIELDS = 'sequence,host_seconds,active,before,candidate,cancel,hold_now_ms,last_write_ms,timeout,detector_ms,trigger_ms,mix_ms,dt,event,arrival,rise,shaped,mixed,out,sink_host_seconds,rumble_request'.split(',')
f32 = lambda v: struct.unpack('f', struct.pack('f', v))[0]


def fixture(strength, enhanced):
    # Rise, repeated millisecond, negative impulse, cancellation, watchdog.
    samples = [(0,0,0,0,0,0,0), (100,32767,0,0,1,1,1),
               (100,0,0,0,0,1,1), (400,-32767,0,0,0,1,0),
               (404,0,1,0,0,0,0), (410,32767,0,0,1,1,1),
               (1000,32767,0,1,0,0,0), (1004,0,1,0,0,0,0)]
    result=[]; applied=0; previous=0
    for i,(ms,before,cancel,timeout,event,arrival,rise) in enumerate(samples,1):
        want=0 if timeout else before
        shaped=f32(want/32767.) if enhanced else f32(f32(want/32767.)*f32((strength//2)/50.))
        # All enhanced nonzero cues are sampled at trigger or after expiry.
        mixed=f32(f32(strength/100.)*f32(shaped*.75)) if enhanced else shaped
        out=int(abs(mixed)*32767+.5)*(1 if mixed>=0 else -1)
        host=ms/1000.; changed=out!=applied;applied=out
        rumble=f32(f32(f32(arrival)*f32(40)/100.)*f32(strength)/100.) if event and not enhanced else 0.
        result.append(dict(zip(FIELDS,[i,host,1,before,want,cancel,ms if before else -1,
            410 if timeout else (ms if before else -1),timeout,ms,
            ms if event and enhanced else -1,ms if enhanced else -1,f32((ms-previous)/1000.),
            event,arrival,rise,shaped,mixed,out,host if changed else -1,rumble])))
        previous=ms
    return result


def envelope_fixture(strength):
    rows=fixture(strength,True)
    for index,ms,fraction in ((3,105,.25),(4,160,-.0625)):
        mixed=f32(f32(strength/100.)*fraction)
        out=int(abs(mixed)*32767+.5)*(1 if mixed>=0 else -1)
        row=dict(zip(FIELDS,[0,ms/1000.,1,0,0,0,-1,-1,0,ms,-1,ms,0,
                            0,0,0,0,mixed,out,ms/1000. if strength else -1,0]))
        rows.insert(index,row)
    previous=0
    for i,row in enumerate(rows,1):
        row['sequence']=i;row['dt']=f32(row['host_seconds']-previous);previous=row['host_seconds']
    # The added zero samples provide the minimum for the later negative arrival.
    # Its 300 ms separation permits a third candidate, at the same instant as mix.
    rows[5]['event']=1;rows[5]['rise']=1;rows[5]['trigger_ms']=400
    return rows


def main():
    exe=Path(sys.argv[1]).resolve(); root=Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/'ticks.csv'
        def run(rows,strength=50,enhanced=False,ok=True,events=2):
            with path.open('w',newline='') as f:
                writer=csv.DictWriter(f,fieldnames=FIELDS,lineterminator='\n');writer.writeheader();writer.writerows(rows)
            p=subprocess.run([str(exe),str(path),str(root/'lib/toolkit/profiles'),'cruisn-vunit@2',
                str(strength),'0','500',str(int(enhanced)),'40'],capture_output=True,text=True)
            assert (p.returncode==0)==ok,(p.stdout,p.stderr)
            if ok:
                r=json.loads(p.stdout);assert (r['ticks'],r['events'],r['cancels'],r['timeouts'])==(len(rows),events,2,1)
        for strength in (0,25,50,80,100):
            for enhanced in (False,True):run(fixture(strength,enhanced),strength,enhanced)
            run(envelope_fixture(strength),strength,True,events=3)
        bad=[(1,'sequence',1),(1,'host_seconds',-1),(1,'shaped',.1),(1,'out',7),
             (1,'event',0),(1,'rise',.2),(1,'candidate',12),(1,'sink_host_seconds',-1),
             (1,'rumble_request',0),(6,'timeout',0),(6,'last_write_ms',1000),
             (1,'dt','nan'),(1,'mix_ms',0),(1,'active',0)]
        for index,key,value in bad:
            rows=fixture(50,False);rows[index][key]=value;run(rows,ok=False)
    print('PASS 15 hand-calculated worker schedules and 14 corrupt-input rejections')


if __name__=='__main__':main()
