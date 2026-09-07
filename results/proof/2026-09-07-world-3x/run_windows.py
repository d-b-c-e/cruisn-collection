from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'harness'))
import replay
from compare_world_motion import compare
from gl_frames import compare_completed_frames
from verification import write_json
work=Path(__file__).resolve().parent
report={'completed':False,'scope':'Bounded Lua visual attribution; not native performance','runs':[]}
for name in ('original','far2-lead8','far3-lead8','far2-lead12','far3-lead12'):
    code=replay.main([str(ROOT/'results/diagnostics/world-germany-extended-20260906'),'--candidate','E:/Source/mame-src/vunit.exe','--output',str(work/name),'--until-frame','6304','--probe-script',str(work/(name+'.lua')),'--scenery','off','--scenery-lead','0','--small-window','--gl-capture','5900:6300','--gl-every','2','--gl-max','201','--timeout','420'])
    evidence=json.loads((work/name/'report.json').read_text())
    assert not evidence.get('error'),evidence.get('error')
    assert not evidence['comparison']['input_or_time_mismatches']
    if name=='original':assert code==0
    item={'name':name,'original_identity_exit':code,'comparison':evidence['comparison']}
    if name!='original':
        item['motion_vs_original']=compare(work/'original/run',work/name/'run')
        item['gl_vs_original']=compare_completed_frames(work/'original/run/gl-snap',work/name/'run/gl-snap',range(5900,6301,2),True)
    report['runs'].append(item)
    write_json(work/'report.json',report)
report['completed']=True
write_json(work/'report.json',report)
