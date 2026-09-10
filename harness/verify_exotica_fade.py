"""Check bounded actual Exotica fade writes; lifecycle membership stays outside scope."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import subprocess
import sys

MAX_EVENTS=8192

def word(value):
    if type(value) is not int or not 0<=value<=0xffffffff:
        raise ValueError('unsigned32 fade operand required')
    return value

def step(packed,flags,increment):
    """Independent byte-lane expression of the captured render-field update."""
    packed,flags,increment=map(word,(packed,flags,increment))
    lanes=bytearray(packed.to_bytes(4,'little'))
    source=lanes[2]+increment
    if not flags&0x04000000 or not 1<=increment<=255 or source>255:
        raise ValueError('fade step outside bounded active domain')
    lanes[2]=source;lanes[3]=(256-source)//2
    completed=source>=247
    return int.from_bytes(lanes,'little'),flags&~0x04000100 if completed else flags,completed

def verify(directory,native=None):
    directory=Path(directory)
    receipt_path=directory/'exotica-fade-capture.json';events_path=directory/'exotica-fade-events.jsonl'
    if receipt_path.stat().st_size>65536 or events_path.stat().st_size>4*1024*1024:
        raise ValueError('fade capture file budget')
    receipt=json.loads(receipt_path.read_text(encoding='utf-8'))
    rows=[json.loads(line) for line in events_path.read_text(encoding='utf-8').splitlines()]
    if receipt.get('complete') is not True or receipt.get('error') is not None or not 1<=len(rows)<=MAX_EVENTS or type(receipt.get('events')) is not int or receipt['events']!=len(rows):
        raise ValueError('incomplete or empty fade capture')
    windows=receipt.get('windows')
    if windows is not None:
        if not isinstance(windows,list) or not 1<=len(windows)<=16:
            raise ValueError('fade window bounds')
        end=0;total=0
        for window in windows:
            if not isinstance(window,list) or len(window)!=2:
                raise ValueError('fade window bounds')
            a,b=map(word,window)
            if not 1800<=a<=b<=16000 or a<=end:raise ValueError('fade window bounds')
            total+=b-a+1;end=b
        if total>240:raise ValueError('fade window budget')
    inputs=[];expected=[];counts=Counter();first=None;last=None;previous=(-1,-1.)
    for index,row in enumerate(rows,1):
        if type(row['id']) is not int or row['id']!=index:
            raise ValueError('fade event identity')
        frame,native_frame=word(row['frame']),word(row['native_frame'])
        when=row['time'];obj=word(row['object'])
        if (not 1800<=frame<=16000 or frame-native_frame not in (0,1) or
                not isinstance(when,(int,float)) or isinstance(when,bool) or not math.isfinite(when) or when<0 or
                frame<previous[0] or when<previous[1] or not 0x1000<=obj<0x40000-32):
            raise ValueError('fade event frame/time/owner bounds')
        if windows is not None and not any(a<=frame<=b for a,b in windows):
            raise ValueError('fade event outside declared windows')
        previous=frame,when;first=frame if first is None else first;last=frame
        packed,flags,increment=map(word,(row['before'],row['flags_before'],row['increment']))
        actual=word(row['actual']),word(row['flags_after'])
        result=step(packed,flags,increment)
        if actual!=result[:2]:raise ValueError(f'fade write mismatch at event{index}')
        inputs.append((packed,flags,increment));expected.append([result[0],result[1],int(result[2])])
        counts['completed' if result[2] else 'continuing']+=1;counts['increment_'+str(increment)]+=1
    if native is not None:
        native=Path(native).resolve()
        process=subprocess.run([str(native)],input=''.join(' '.join(map(str,row))+'\n' for row in inputs),
            capture_output=True,text=True,timeout=60)
        if process.returncode:raise ValueError(f'native fade analyzer exit{process.returncode}: {process.stderr[:300]}')
        if [list(map(int,line.split())) for line in process.stdout.splitlines()]!=expected:
            raise ValueError('native fade write mismatch')
    return dict(schema=1,passed=True,events=len(rows),first_frame=first,last_frame=last,counts=dict(counts),windows=windows,
        native_verified=native is not None,native_sha256=hashlib.sha256(native.read_bytes()).hexdigest() if native else None,
        sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (receipt_path,events_path)},
        scope=__doc__+' Original route/pixels, full lifecycle and a host handover policy require separate checks.')

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path)
    p.add_argument('--native',type=Path);p.add_argument('--report',type=Path,required=True);a=p.parse_args()
    try:result=verify(a.directory,a.native)
    except (ValueError,KeyError,TypeError,OSError,subprocess.TimeoutExpired) as e:result=dict(schema=1,passed=False,error=str(e))
    a.report.parent.mkdir(parents=True,exist_ok=True)
    a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('PASS' if result['passed'] else 'FAIL',a.report);return 0 if result['passed'] else 1

if __name__=='__main__':sys.exit(main())
