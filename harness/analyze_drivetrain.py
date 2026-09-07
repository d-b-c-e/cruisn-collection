"""Check USA drivetrain traces against independent RAM probes and real UDP packets."""
import argparse
import csv
import json
import math
from pathlib import Path

from verification import sha256_file, write_json


def c31(word):
    word=int(word,16)
    if word==0x80000000:return 0.0
    exponent=word>>24
    if exponent>=128:exponent-=256
    return math.ldexp((-2 if word&0x800000 else 1)+(word&0x7fffff)/8388608,exponent)


def analyze(directory, memory=None, require_drive=False):
    directory=Path(directory)
    path=directory/'drivetrain.csv'
    rows=list(csv.DictReader(path.open()))
    if not rows:raise ValueError('empty drivetrain trace')
    report={'passed':False,'trace_sha256':sha256_file(path),'samples':len(rows)}
    frames=[int(r['frame']) for r in rows]
    if any(b<=a for a,b in zip(frames,frames[1:])):raise ValueError('duplicate/reversed frame samples')
    active=[r for r in rows if r['gear_source']=='3']
    for r in rows:
        rpm,fraction,rev=map(float,(r['rpm'],r['tach_fraction'],r['rev_value']))
        if not all(math.isfinite(v) for v in (rpm,fraction,rev)):raise ValueError('nonfinite drivetrain')
        if not 0<=fraction<=1 or not 0<=rpm<=8000 or not 0<=int(r['gear'])<=4:raise ValueError('drivetrain outside bounds')
        if r['rpm_estimated']=='0' and rpm!=0:raise ValueError('unavailable RPM must clear')
        if r['rpm_estimated']=='1' and (r['gear_source']!='3' or rpm<900):raise ValueError('estimated RPM lacks game state')
    shifts=[]
    for i,(a,b) in enumerate(zip(rows,rows[1:])):
        if a['gear_source']==b['gear_source']=='3' and 0<int(a['gear'])<int(b['gear']):
            after=[float(r['rpm']) for r in rows[i+1:i+10] if r['gear_source']=='3' and r['gear']==b['gear']]
            shifts.append({'frame':int(b['frame']), 'from':int(a['gear']),'to':int(b['gear']),
                           'rpm_before':float(a['rpm']), 'minimum_next_8_frames':min(after)})
    report.update(game_state_samples=len(active),gears=sorted({int(r['gear']) for r in active}),upshifts=shifts,
                  rpm_range=[min(float(r['rpm']) for r in rows),max(float(r['rpm']) for r in rows)])
    if require_drive and (not {1,2,3,4}<=set(report['gears']) or not shifts or
                          any(s['minimum_next_8_frames']>=s['rpm_before'] for s in shifts)):
        raise ValueError('drive must exercise all four gears and RPM drops on each upshift')
    if memory:
        memory=Path(memory)
        reference={int(r['frame']):r for r in csv.DictReader(memory.open())}
        # session.lua is one-based; native screen.frame_number() is zero-based.
        pairs=[(r,reference[int(r['frame'])+1]) for r in active if int(r['frame'])+1 in reference]
        bad=sum(a['gear']!=b['gear'] or int(a['player'])!=int(b['player'],16) or
                abs(float(a['rev_value'])-c31(b['rev_raw']))>1e-5 for a,b in pairs)
        report['memory']={'sha256':sha256_file(memory),'samples':len(pairs),'mismatches':bad,'lua_frame_offset':1}
        if not pairs or bad:raise ValueError('independent memory-probe mismatch')
    wire=directory/'forza.csv'
    if wire.exists():
        packets=list(csv.DictReader(wire.open()))
        if len(packets)!=len(rows):raise ValueError('missing/extra Forza packets')
        for i,(r,p) in enumerate(zip(rows,packets)):
            if int(p['timestamp_ms'])!=17*(i+1) or int(p['gear'])!=(int(r['gear']) or 1) or abs(float(p['rpm'])-float(r['rpm']))>.001:
                raise ValueError('Forza packet disagrees with emitted sample')
            if float(r['rpm'])>0 and (float(p['max_rpm'])!=8000 or float(p['idle_rpm'])!=900):raise ValueError('Forza gauge limits')
        events=[json.loads(line) for line in (directory/'telemetry.jsonl').read_text().splitlines()]
        for output,column in [('gear','gear'),('gear_source','gear_source'),('rpm_estimated','rpm_estimated'),('rpm','rpm')]:
            values=[e['value'] for e in events if e['out']==output]
            # CSV formats RPM to three decimals. A real 5675.49951171875 is
            # printed as 5675.500, but the integer JSON value is correctly 5675.
            # Compare JSON rounding against the full-precision Forza float.
            source=packets if output=='rpm' else rows
            expected=[int(float(r[column])+.5) for r in source]
            if values!=expected:raise ValueError(f'JSON {output} disagrees with emitted samples')
        report['wire']={'forza_packets':len(packets),'json_packets':len(events),'passed':True}
    report['passed']=True
    return report


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('directory',type=Path);ap.add_argument('--memory',type=Path)
    ap.add_argument('--require-drive',action='store_true');ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    try:report=analyze(args.directory,args.memory,args.require_drive)
    except (ValueError,KeyError,OSError) as error:report={'passed':False,'error':str(error)}
    write_json(args.output,report);print(json.dumps(report,indent=2))
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
