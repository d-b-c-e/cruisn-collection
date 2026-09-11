"""Time-weight actual force output inside explicitly bounded game-time windows.

Clock conversion uses source anchors, not linear interpolation. Only the host
interior known to lie inside a window is measured. Unknown edges are reported.
This does not classify contacts, fit gains or establish physical acceptance.
"""
import argparse
import bisect
import csv
import json
import math
from pathlib import Path

import ffb_worker
from force_segments import nanoseconds, integer, read_csv, SOURCE
from verification import sha256_file, write_json

NS = 1_000_000_000


class ClockMap:
    def __init__(self, anchors):
        if len(anchors) < 2 or len(anchors) > 131072:
            raise ValueError('source anchor count')
        if any(not isinstance(v, int) or isinstance(v, bool) or v < 0 for pair in anchors for v in pair):
            raise ValueError('source anchor integer clocks')
        if any(a[0] > b[0] or a[1] > b[1] for a,b in zip(anchors,anchors[1:])):
            raise ValueError('source anchor clocks go backwards')
        self.emulated = [a for a,_ in anchors]
        self.host = [b for _,b in anchors]

    def interior(self, start, end):
        if not isinstance(start,int) or not isinstance(end,int) or not 0 <= start < end:
            raise ValueError('invalid emulated window')
        # A 1 ns guard covers rounding of each recorded emulated timestamp.
        # Choose anchors strictly inside both guarded edges. Duplicate emulated
        # times remain distinct host observations and must not be collapsed.
        first = bisect.bisect_left(self.emulated, start+1)
        after = bisect.bisect_left(self.emulated, end-1)
        before_start = bisect.bisect_left(self.emulated, start-1)-1
        after_end = bisect.bisect_left(self.emulated, end+1)
        if before_start < 0 or first == len(self.host) or after_end == len(self.host):
            return dict(usable=False, reason='unbracketed_boundary')
        last = after-1
        if last <= first:
            return dict(usable=False, reason='no_known_host_interior')
        a,b = self.host[first]+1, self.host[last]-1
        if b <= a:
            return dict(usable=False, reason='no_known_host_interior')
        return dict(usable=True, start_ns=a, end_ns=b,
                    start_bounds_ns=[max(0,self.host[before_start]-1), self.host[first]+1],
                    end_bounds_ns=[self.host[last]-1, self.host[after_end]+1],
                    boundary_uncertainty_ns=(self.host[first]-self.host[before_start]
                                              + self.host[after_end]-self.host[last]+4),
                    largest_internal_anchor_gap_ns=max(
                        self.host[i+1]-self.host[i] for i in range(first,last)))


def held_output(ticks, stop_ns):
    if not ticks:
        raise ValueError('missing force ticks')
    changes=[];previous=0;last_host=-1;last_sink=-1
    for index,row in enumerate(ticks,1):
        if integer(row['sequence'],1,131072) != index:
            raise ValueError('force tick sequence')
        host=nanoseconds(row['host_seconds']);out=integer(row['out'],-32767,32767)
        if host < max(last_host,last_sink):
            raise ValueError('force tick clock')
        if index == 1:changes.append((host,0))
        if out != previous:
            sink=nanoseconds(row['sink_host_seconds'])
            if sink < max(host,last_sink):raise ValueError('force sink clock')
            changes.append((sink,out));last_sink=sink
        elif row['sink_host_seconds'] != '-1':
            raise ValueError('unexpected force sink update')
        previous=out;last_host=host
    if stop_ns < max(last_host,last_sink):raise ValueError('force stop clock')
    changes.append((stop_ns,0))
    return [(a,b,value) for (a,value),(b,_) in zip(changes,changes[1:]) if b>a]


def measure(held, windows, ceiling):
    if not 0 <= ceiling <= 32767:raise ValueError('force ceiling')
    distribution={};positive=negative=zero=saturated=near_ceiling=0;selected=[]
    ends=[b for _,b,_ in held]
    if any(a>=b or abs(v)>32767 for a,b,v in held) or any(x[1]!=y[0] for x,y in zip(held,held[1:])):
        raise ValueError('held output order/range')
    previous_end=-1
    for start,end in windows:
        if not 0 <= start < end or start < previous_end:raise ValueError('overlapping host windows')
        previous_end=end;covered=0
        for index in range(bisect.bisect_right(ends,start),len(held)):
            a,b,value=held[index]
            if a>=end:break
            a,b=max(a,start),min(b,end)
            if b<=a:continue
            dt=b-a;covered+=dt;distribution[abs(value)]=distribution.get(abs(value),0)+dt
            if value>0:positive+=dt
            elif value<0:negative+=dt
            else:zero+=dt
            if ceiling and abs(value)>=ceiling:saturated+=dt
            if ceiling and abs(value)*100>=ceiling*99:near_ceiling+=dt
            selected.append((a,b,value))
        if covered != end-start:raise ValueError('host output coverage gap')
    total=positive+negative+zero
    if total==0:return dict(seconds=0,intervals=0)
    def q(fraction):
        target=total*fraction;current=0
        for value,weight in sorted(distribution.items()):
            current+=weight
            if current>=target:return value/32767
    return dict(seconds=total/NS,intervals=len(windows),absolute_p50=q(.5),absolute_p90=q(.9),
                rms=math.sqrt(sum(v*v*w for v,w in distribution.items())/total)/32767,
                peak_abs=max(distribution)/32767,positive_seconds=positive/NS,
                negative_seconds=negative/NS,zero_seconds=zero/NS,
                requested_ceiling_fraction=saturated/total,
                within_one_percent_of_ceiling_fraction=near_ceiling/total,
                absolute_impulse_normalized_seconds=sum(abs(v)*(b-a) for a,b,v in selected)/(32767*NS),
                signed_impulse_normalized_seconds=sum(v*(b-a) for a,b,v in selected)/(32767*NS))


def analyze(directory, specification):
    directory=Path(directory)
    replay=json.loads((directory.parent/'report.json').read_text(encoding='utf-8'))
    invocation=json.loads((directory/'invocation.json').read_text(encoding='utf-8'))
    trial=replay.get('ffb_worker',{});verified=trial.get('result',{})
    if (replay.get('passed') is not True or verified.get('passed') is not True or
            trial.get('mode') != 'observe' or invocation['environment'].get('MIDV_FFB') != '0' or
            verified.get('physical_acceptance') is not False):
        raise ValueError('requires an accepted device-free worker replay')
    if any(sha256_file(directory/name)!=verified['hashes'].get(name) for name in ffb_worker.FILES):
        raise ValueError('worker journal/receipt changed since stage verification')
    receipt=json.loads((directory/ffb_worker.FILES[0]).read_text(encoding='ascii'))
    if receipt != verified['receipt'] or not receipt['complete'] or receipt['sink_final_level'] != 0:
        raise ValueError('worker completion receipt mismatch')
    if specification.get('schema') != 1 or specification.get('clock') != 'emulated_nanoseconds':
        raise ValueError('window schema/clock')
    if not isinstance(specification.get('reviewed'),bool):raise ValueError('explicit review status required')
    if specification['reviewed'] and not all(isinstance(specification.get(k),str) and specification[k].strip()
                                               for k in ('reviewer','evidence_notes')):
        raise ValueError('reviewed windows need reviewer and visual evidence notes')
    for key,name in (('force_source_sha256','force-source.csv'),('frames_sha256','frames.csv')):
        if specification.get(key)!=sha256_file(directory/name):raise ValueError('window game-source binding')
    if sha256_file(directory/'frames.csv') != replay['evidence']['trace_sha256']:
        raise ValueError('recorded input trace changed since replay')
    windows=specification.get('windows',[])
    if not windows or len(windows)>200000:raise ValueError('window count')
    anchors=ffb_worker.bounded_sources(directory/ffb_worker.FILES[2])
    source=read_csv(directory/'force-source.csv',SOURCE)
    if len(source)!=len(anchors) or len(source)!=verified['source_join_rows'] or any(
            int(s['raw'])!=a['raw'] or int(s['adapted'])!=a['adapted'] or int(s['frame'])!=a['frame'] or
            abs(nanoseconds(s['seconds'])-nanoseconds(a['emulated_seconds']))>1 for s,a in zip(source,anchors)):
        raise ValueError('original source no longer joins worker anchors')
    clock=ClockMap([(nanoseconds(r['emulated_seconds']),nanoseconds(r['host_seconds'])) for r in anchors])
    ticks=read_csv(directory/ffb_worker.FILES[1])
    held=held_output(ticks,nanoseconds(receipt['stop_host_seconds']))
    if not held:raise ValueError('no observed output duration')
    strength=receipt['strength']/100 if receipt['impact_axis'] else (receipt['strength']//2)/50
    ceiling=int(math.floor(strength*32767+.5))
    groups={};joins=[];previous_end=-1;ids=set()
    for window in windows:
        start,end=window['start_ns'],window['end_ns'];kind=window.get('kind');ident=window.get('id')
        if (not isinstance(kind,str) or not 0<len(kind)<=160 or not isinstance(ident,str) or
                not 0<len(ident)<=160 or ident in ids or not isinstance(start,int) or
                not isinstance(end,int) or isinstance(start,bool) or isinstance(end,bool) or
                not 0<=start<end or start<previous_end):
            raise ValueError('window order/range/identity')
        ids.add(ident);previous_end=end
        join=clock.interior(start,end)
        if join['usable'] and (join['start_ns']<held[0][0] or join['end_ns']>held[-1][1]):
            join=dict(usable=False,reason='outside_observed_output')
        joins.append(dict(window,host=join))
        if join['usable']:groups.setdefault(kind,[]).append((join['start_ns'],join['end_ns']))
    return dict(schema=1,passed=True,kind='observed-worker-window-measurement',
                normalization_accepted=False,physical_acceptance=False,windows_reviewed=specification['reviewed'],
                scope='Time-weighted software sink, conservative clock interiors; receipt hashes bind prior stage verification',
                nominal_strength=trial['nominal_strength'],effective_strength=receipt['strength'],
                impact_axis=receipt['impact_axis'],candidate_sha256=invocation['executable_sha256'],
                input_hashes={name:sha256_file(directory/name) for name in (*ffb_worker.FILES,'force-source.csv','frames.csv','invocation.json')},
                replay_report_sha256=sha256_file(directory.parent/'report.json'),
                joins=joins,groups={kind:measure(held,values,ceiling) for kind,values in sorted(groups.items())})


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path);parser.add_argument('windows',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args(argv);args.output.mkdir(parents=True,exist_ok=False)
    try:
        if args.windows.stat().st_size>64*1024*1024:raise ValueError('window file size')
        result=analyze(args.run,json.loads(args.windows.read_text(encoding='utf-8')))
        result['windows_sha256']=sha256_file(args.windows)
    except (ValueError,OSError,KeyError,TypeError) as error:
        result=dict(passed=False,normalization_accepted=False,error=str(error))
    write_json(args.output/'report.json',result)
    print(('PASS' if result['passed'] else 'FAIL')+': '+str(args.output/'report.json'))
    return 0 if result['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
