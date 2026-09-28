"""Compare passing World control/trial indexed ownership at one completed frame."""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image

from gl_frames import capture_paths, read_completed_frames
from screen_world_active_gap import component


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def planes(root, frame, page):
    paths = [root/'run'/f'vunit-mirror-{frame}-page{page}-plane{i}.bin' for i in range(4)]
    values = [np.fromfile(path, dtype='<u2' if i%2==0 else 'u1').reshape(1600,2736)
              for i,path in enumerate(paths)]
    return paths,values


def completed_path(root, report, frame):
    captures = report['evidence']['gl_captures']
    directory = root/'run'/'gl-snap'
    signatures = read_completed_frames(directory,captures['completed_frames'])
    if frame not in signatures:
        raise ValueError('requested completed frame is absent or ambiguous')
    path = capture_paths(directory)[frame]
    if signatures[frame] != captures['files'][path.name]:
        raise ValueError('completed image does not match its replay receipt')
    return path


def compare(control, trial, geometry_paths):
    a = json.loads((control/'report.json').read_text(encoding='utf-8'))
    b = json.loads((trial/'report.json').read_text(encoding='utf-8'))
    if (not a.get('passed') or not b.get('passed') or a['case'] != b['case'] or
            not a['comparison']['passed'] or not b['comparison']['passed'] or
            not a['display_watch']['passed'] or not b['display_watch']['passed']):
        raise ValueError('matched input/native/display replay has not passed')
    am = a['vunit_original_mirror']['result']
    bm = b['vunit_original_mirror']['result']
    frame,page = am['frame'],am['visible_page']
    source = am['host_completion']['visible']['frame']
    if (bm['frame'] != frame or bm['visible_page'] != page or
            bm['host_completion']['visible']['frame'] != source or
            not bm['fade_metadata']['captured_nonroad_margins']):
        raise ValueError('candidate is not a margin-active source/display pair')
    original_exact = True
    center_exact = True
    changed = prior_owned = newly_owned = 0
    visible_control = visible_trial = None
    plane_hashes = {}
    for p in range(2):
        paths_a,aa = planes(control,frame,p)
        paths_b,bb = planes(trial,frame,p)
        plane_hashes.update({f'control_{path.name}':sha(path) for path in paths_a})
        plane_hashes.update({f'trial_{path.name}':sha(path) for path in paths_b})
        original_exact &= all(np.array_equal(x,y) for x,y in zip(aa[2:],bb[2:]))
        center_exact &= all(np.array_equal(x[:,344:2392],y[:,344:2392])
                            for x,y in zip(aa[:2],bb[:2]))
        if p==page:
            visible_control,visible_trial = aa,bb
            margin=np.zeros_like(aa[1],dtype=bool)
            margin[:,:344]=True;margin[:,2392:]=True
            delta=margin & ((aa[0]!=bb[0]) | (aa[1]!=bb[1]))
            changed=int(delta.sum())
            prior_owned=int((delta & (aa[1]!=0)).sum())
            newly_owned=int((delta & (aa[1]==0) & (bb[1]!=0)).sum())
    if not original_exact or not center_exact:
        raise ValueError('original indexed planes or 4:3 center changed')
    gaps={}
    for name,path in geometry_paths.items():
        geometry=json.loads(path.read_text(encoding='utf-8'))
        if (geometry['source_frame']!=source or geometry['completed_frame']!=frame or
                geometry['page']!=page):
            raise ValueError('gap geometry does not match visible source/page')
        mask=component(visible_control,geometry)
        gained=mask & (visible_trial[1]!=0)
        gaps[name]={'control_gap_pixels':int(mask.sum()),
                    'trial_owned_pixels':int(gained.sum()),
                    'remaining_unowned_pixels':int((mask & (visible_trial[1]==0)).sum())}
    control_completed = completed_path(control,a,frame)
    trial_completed = completed_path(trial,b,frame)
    left=np.asarray(Image.open(control_completed).convert('RGB'))
    right=np.asarray(Image.open(trial_completed).convert('RGB'))
    if left.shape!=right.shape:
        raise ValueError('completed image dimensions differ')
    ys,xs=np.where(np.any(left!=right,axis=2))
    return {'passed':bool(gaps and all(v['trial_owned_pixels']>0 for v in gaps.values())
                          and len(xs)>0),
            'scope':'One completed World frame with matched input/native evidence and exact '
                    'original/center indexed planes. No temporal or other-course acceptance.',
            'frame':frame,'page':page,'source_frame':source,
            'nonroad_margin_packets':bm['fade_metadata']['captured_nonroad_margins'],
            'original_indexed_planes_exact':original_exact,'center_indexed_exact':center_exact,
            'margin_changed_indexed_pixels':changed,
            'margin_newly_owned_pixels':newly_owned,
            'margin_previously_owned_changed_pixels':prior_owned,
            'gaps':gaps,'completed_rgb_changed_pixels':len(xs),
            'completed_rgb_changed_bounds':([int(xs.min()),int(ys.min()),
                                             int(xs.max()),int(ys.max())] if len(xs) else None),
            'sha256':{'control_report':sha(control/'report.json'),
                      'trial_report':sha(trial/'report.json'),
                      'control_completed':sha(control_completed),
                      'trial_completed':sha(trial_completed),
                      **plane_hashes,
                      **{f'{name}_geometry':sha(path) for name,path in geometry_paths.items()}}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--control',type=Path,required=True)
    parser.add_argument('--trial',type=Path,required=True)
    parser.add_argument('--left-geometry',type=Path)
    parser.add_argument('--right-geometry',type=Path)
    parser.add_argument('--report',type=Path,required=True)
    args=parser.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite paired frame evidence')
    paths={name:path for name,path in (('left',args.left_geometry),('right',args.right_geometry)) if path}
    result=compare(args.control,args.trial,paths)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('PASS' if result['passed'] else 'FAIL',result['gaps'],
          'center exact',result['center_indexed_exact'])
    if not result['passed']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
