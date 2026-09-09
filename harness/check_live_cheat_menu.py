"""Record real Esc/Cheats/resume key-handler transitions, then replay the actions.

Uses an immutable driving case, imported exact-revision XML and isolated state.
No global input injection or physical force. This opens a game window.
"""
import argparse
import json
from pathlib import Path
import re

import numpy as np
from PIL import Image
import cheats
from derive_case import inherited_settings, validate_parent
from diagnostic_runtime import ROOT, diagnostic_env, execute, new_run
from display_target import choose_size, monitors, parse_size
import replay
from session_case import Recording, set_option
from verification import sha256_file, write_json


def inspect(runtime, rom):
    log = (runtime/('midz_gl.log' if rom == 'crusnexo' else 'midv_gl.log')).read_text(encoding='utf-8',errors='replace')
    rows = [dict(zip(('step','open','selected','crt','frame','new_frame'),map(int,m))) for m in re.findall(
        r'menu snapshot step=(\d+) open=(\d+) selected=(\d+) crt=(\d+) completed_frame=(\d+) new_frame=(\d+)',log)]
    details = [tuple(map(int,m)) for m in re.findall(
        r'cheat menu snapshot step=(\d+) submenu=(\d+) entries=(\d+) pending=(\d+)',log)]
    if [r['step'] for r in rows] != list(range(9)) or [r[0] for r in details] != list(range(9)):
        raise ValueError('missing live cheat menu captures')
    if [(r['open'],r['selected']) for r in rows] != [(1,0),(1,1),(1,2),(1,2),(1,2),(1,2),(0,2),(1,2),(1,3)]:
        raise ValueError('incorrect Esc/Cheats/Back/Resume/Exit navigation')
    if [r[1] for r in details] != [0,0,0,1,1,0,0,0,0] or not all(r[2] > 0 for r in details):
        raise ValueError('cheat catalog or submenu was not shown')
    if [r[3] for r in details] != [0,0,0,0,1,1,0,0,0]:
        raise ValueError('cheat was not staged exactly once and submitted only on resume')
    if len({r['frame'] for r in rows[1:6]}) != 1 or rows[7]['frame'] <= rows[5]['frame']:
        raise ValueError('game did not stay paused and then resume')
    if len({r['crt'] for r in rows}) != 1 or 'menu test step=9' not in log:
        raise ValueError('cheat menu changed CRT or did not reach Exit')
    for row in rows:
        path=runtime/'gl-snap'/f"menu_{row['step']:02d}.bmp"
        pixels=np.asarray(Image.open(path).convert('RGB'))
        gold=(pixels[:,:,0]>220)&(pixels[:,:,1]>120)&(pixels[:,:,1]<215)&(pixels[:,:,2]<90)
        if row['open'] and int(gold.sum()) < 500: raise ValueError('menu text is not visibly rendered')
        row['image_sha256']=sha256_file(path)
    if rows[3]['image_sha256']==rows[4]['image_sha256']:
        raise ValueError('staged cheat selection did not redraw')
    selection=json.loads((runtime/'cheats/selection.json').read_text(encoding='utf-8'))
    actions=cheats.read_actions(runtime/'cheats/actions.csv',selection,100000000)
    if len(actions)!=1 or (actions[0]['index'],actions[0]['steps'],actions[0]['activate'])!=(1,1,0):
        raise ValueError('live menu did not execute exactly one timer selection')
    return {'menu':rows,'actions':actions}


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('case',type=Path); ap.add_argument('--candidate',required=True,type=Path)
    ap.add_argument('--archive',type=Path,help='default: imported exact-revision XML in the personal rig, read-only')
    ap.add_argument('--frame',type=int,default=2700); ap.add_argument('--output')
    ap.add_argument('--timeout',type=int,default=150)
    ap.add_argument('--display-size',type=parse_size,default=(3840,2160),help='actual display WIDTH:HEIGHT; default 3840:2160, with a maximized game window')
    args=ap.parse_args(argv)
    work=new_run('live-cheat-menu',args.output)
    report={'passed':False,'physical_force':False,'candidate_sha256':sha256_file(args.candidate)}
    try:
        parent=args.case.resolve(); manifest=json.loads((parent/'case.json').read_text(encoding='utf-8'))
        validate_parent(parent,manifest)
        if not 1200 <= args.frame < manifest['evidence']['frames']-120:
            raise ValueError('menu test must run after boot and within the drive')
        source=args.archive or ROOT/'rig/cheats'/(manifest['rom']+'.xml')
        cheats.import_files(source,work/'import')
        cat=cheats.catalog(work/'import',manifest['rom'])
        if not cat['entries'] or cat['entries'][0]['description']!='Infinite Time':
            raise ValueError('this diagnostic requires Infinite Time as the first imported entry')
        bundle=cheats.prepare(ROOT,work/'import',manifest['rom'])
        command=list(manifest['command']); command[0]=str(args.candidate.resolve())
        command=[arg for arg in command if arg not in ('-nocheat','-maximize','-nomaximize','-nowindow')]+['-cheat','-window','-maximize','-throttle']
        target=choose_size(args.display_size,monitors())
        report['display_target']=target
        for option,value in (('-screen',target['selected']['device']),('-resolution','x'.join(map(str,args.display_size))),('-sound','none'),('-video','d3d')):
            command=set_option(command,option,value)
        settings=inherited_settings(parent,manifest['settings'])
        settings.update(MIDV_CHEATS=str(bundle),MIDV_GL_LOG='1',MIDZ_GL_LOG='1')
        for key in list(settings):
            if '_SNAP' in key: settings.pop(key)
        if manifest['rom']=='crusnexo': settings['MIDZ_GL']='1'
        else: settings['MIDV_GL']='1'
        prefix='MIDZ' if manifest['rom']=='crusnexo' else 'MIDV'
        settings[prefix+'_GL_SNAP']='redirect-at-launch'
        settings[prefix+'_GL_SNAP_EVERY']='300'
        settings[prefix+'_GL_SNAP_FIRST']='1200'
        recording=Recording(work/'case',every=60,stop_frame=manifest['evidence']['frames'],snapshot_mode='raw')
        command,env,runtime=recording.prepare(command,diagnostic_env(settings),parent/'initial',stimulus=parent/'record/input/session.inp')
        (runtime/'gl-snap').mkdir(exist_ok=True)
        # UI stimulus belongs only to this run, never the replay manifest.
        env['MIDV_CHEAT_MENU_TEST_FRAME']=str(args.frame)
        result=execute(command,runtime,env,args.timeout)
        (runtime/'launch.log').write_bytes((runtime/'stdout.log').read_bytes())
        recording.finish(result['returncode'])
        if result['error'] or recording.manifest['status']!='recorded':
            raise ValueError(result['error'] or recording.manifest.get('error','recording incomplete'))
        report.update(inspect(runtime,manifest['rom']))
        # Reuse the emulator/input/starting-state snapshots and actual actions;
        # no menu input is synthesized during playback.
        report['replay_passed']=replay.main([str(recording.path),'--compare-gl','--output',str(work/'replay'),'--timeout',str(args.timeout)])==0
        if not report['replay_passed']: raise ValueError('recorded cheat actions or gameplay did not replay')
        report.update(passed=True,rom=manifest['rom'],frames=recording.manifest['evidence']['frames'],xml_sha256=cat['sha256'])
    except (OSError,ValueError,KeyError) as error: report['error']=str(error)
    write_json(work/'report.json',report)
    print('PASS' if report['passed'] else 'FAIL',work,report.get('error',''),flush=True)
    return 0 if report['passed'] else 1


if __name__=='__main__': raise SystemExit(main())
