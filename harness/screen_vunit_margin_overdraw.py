"""Attribute changed V-Unit margin pixels to original DMA or prior host output.

This one-frame screen validates matched indexed mirrors and current original
DMA. It does not reconstruct the complete ordered host scene or prove temporal
occlusion safety.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from analyze_vunit_margin_gap import projected_box
from offroad_gap_loaded_screen import render_quads
from screen_world_active_overlap import planes
from vunit_display_scene import load as original_scene


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def screen(control, trial, source):
    roots=(control,trial,source)
    reports=[json.loads((root/'report.json').read_text(encoding='utf-8')) for root in roots]
    a,b,s=reports
    if (not all(r['passed'] and r['comparison']['passed'] and
                r['display_watch']['passed'] and
                r['vunit_runtime']['result']['completion']=='owned-worker-stop'
                for r in reports) or
            any(json.loads((root/'run/invocation.json').read_text(encoding='utf-8'))
                ['environment'].get('MIDV_FFB')!='0' for root in roots) or
            len({r['case'] for r in reports})!=1 or
            len({r['emulator_source']['executable_sha256'] for r in reports})!=1 or
            len({json.dumps(r['display_target'],sort_keys=True) for r in reports})!=1):
        raise ValueError('input/native/display/binary/FFB qualification differs')
    receipts=[r['vunit_original_mirror']['result'] for r in reports]
    frame,page=receipts[0]['frame'],receipts[0]['visible_page']
    if any(r['frame']!=frame or r['visible_page']!=page for r in receipts):
        raise ValueError('completed mirror frame/page differs')
    if receipts[0]['sha256']!=receipts[2]['sha256']:
        raise ValueError('original-DMA source replay differs from control mirror')
    gl=[r['evidence']['gl_captures']['files'] for r in reports]
    if len(gl[0])!=1 or gl[0]!=gl[2]:
        raise ValueError('original-DMA source completed image differs from control')
    paths,aa=planes(control,frame,page)
    trial_paths,bb=planes(trial,frame,page)
    if not all(np.array_equal(x,y) for x,y in zip(aa[2:],bb[2:])):
        raise ValueError('original-only mirror planes differ')
    changed=(aa[0]!=bb[0])|(aa[1]!=bb[1])
    if not changed.any() or changed[:,344:2392].any():
        raise ValueError('no visible indexed change or center damage')
    if np.any(changed & ((bb[1]&4)==0)):
        raise ValueError('changed candidate pixel lacks host ownership tag')
    guest=changed & (aa[1]!=0) & ((aa[1]&4)==0)
    host=changed & ((aa[1]&4)!=0)
    fresh=changed & (aa[1]==0)
    original_exact=guest & (aa[0]==aa[2]) & (aa[1]==aa[3])
    scene=original_scene(source/'run').current
    texture=source/'run/capture/textureram.bin'
    index,tags=render_quads(scene,texture.read_bytes())
    ids,idtags=render_quads(scene,texture.read_bytes(),debug_quad_id=True)
    reconstructed=original_exact & (tags!=0) & (idtags!=0) & (aa[0]==index)
    if int(reconstructed.sum())!=int(guest.sum()):
        raise ValueError('current original DMA does not explain every overwritten game pixel')
    ordinals,counts=np.unique(ids[reconstructed],return_counts=True)
    attributed=[{'original_dma_ordinal':int(i),'changed_pixels':int(n),
                 'native_box':projected_box(tuple(map(int,scene[int(i)]))),
                 'quad_sha256':hashlib.sha256(np.asarray(scene[int(i)],dtype='<u2').tobytes()).hexdigest()}
                for i,n in zip(ordinals,counts)]
    attributed.sort(key=lambda row:row['changed_pixels'],reverse=True)
    ys,xs=np.where(changed)
    return {'passed':True,
            'scope':'One matched completed V-Unit indexed page and current original DMA. '
                    'Prior host pixel source, full compositing and temporal safety are unqualified.',
            'rom':json.loads((Path(a['case'])/'case.json').read_text(encoding='utf-8'))['rom'],
            'frame':frame,'visible_page':page,
            'input_frames':[r['comparison_scope']['last_frame'] for r in reports],
            'completed_control_equals_original_source':True,
            'original_only_planes_exact':True,'center_4by3_exact':True,
            'changed_indexed_pixels':int(changed.sum()),
            'changed_newly_owned_pixels':int(fresh.sum()),
            'changed_prior_game_pixels':int(guest.sum()),
            'changed_prior_host_pixels':int(host.sum()),
            'changed_prior_game_exact_original_only_pixels':int(original_exact.sum()),
            'changed_prior_game_exact_current_dma_pixels':int(reconstructed.sum()),
            'changed_prior_game_dma_attribution':attributed,
            'control_tag_counts':{str(int(tag)):int(count) for tag,count in
                                  zip(*np.unique(aa[1][changed],return_counts=True))},
            'trial_tag_counts':{str(int(tag)):int(count) for tag,count in
                                zip(*np.unique(bb[1][changed],return_counts=True))},
            'changed_bounds':[int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())],
            'sha256':{'control_report':sha(control/'report.json'),
                      'trial_report':sha(trial/'report.json'),
                      'original_source_report':sha(source/'report.json'),
                      'original_dma':sha(source/'run/capture/quads.bin'),
                      'source_texture':sha(texture),
                      **{f'control_{p.name}':sha(p) for p in paths},
                      **{f'trial_{p.name}':sha(p) for p in trial_paths}}}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('control','trial','source','report'):
        ap.add_argument('--'+name,type=Path,required=True)
    args=ap.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite overdraw evidence')
    result=screen(args.control,args.trial,args.source)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('PASS',result['rom'],result['frame'],result['changed_prior_game_pixels'],
          result['changed_prior_host_pixels'])


if __name__=='__main__':
    main()
