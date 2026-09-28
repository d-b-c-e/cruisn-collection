"""Screen a World active-margin overlap against exact added native packets.

This isolated raster checks material/coverage attribution. It cannot reproduce
the full ordered native compositing of earlier host and original game geometry.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

import numpy as np

from analyze_vunit_margin_gap import PACKET
from offroad_gap_loaded_screen import render_quads


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def packets(path):
    data=path.read_bytes()
    if not data.startswith(b'VFD1') or (len(data)-4)%PACKET.size:
        raise ValueError('invalid fade packet journal')
    return [(tuple(row[3:19]),row[-1]) for row in PACKET.iter_unpack(data[4:])]


def planes(root,frame,page):
    prefix=f'vunit-mirror-{frame}-page{page}-plane'
    paths=[root/'run'/(prefix+str(i)+'.bin') for i in range(4)]
    values=[np.fromfile(path,dtype='<u2' if i%2==0 else 'u1').reshape(1600,2736)
            for i,path in enumerate(paths)]
    return paths,values


def native_scene(path):
    lines=path.read_text(encoding='utf-8').splitlines()
    if not lines:
        raise ValueError('empty native scene')
    header=tuple(int(x) for x in lines[0].split())
    rows=[tuple(int(x) for x in line.split()) for line in lines[1:]]
    if len(header)!=7 or any(len(row)!=24 for row in rows):
        raise ValueError('invalid native scene rows')
    return header,rows


def screen(control,trial,source,projection,native_control,native_trial):
    a=json.loads((control/'report.json').read_text(encoding='utf-8'))
    b=json.loads((trial/'report.json').read_text(encoding='utf-8'))
    s=json.loads((source/'report.json').read_text(encoding='utf-8'))
    p=json.loads(projection.read_text(encoding='utf-8'))
    if (not all(r['passed'] and r['comparison']['passed'] for r in (a,b,s)) or
            a['case']!=b['case'] or a['case']!=s['case'] or
            a['emulator_source']['executable_sha256']!=s['emulator_source']['executable_sha256'] or
            a['evidence']['gl_captures']['files']!=s['evidence']['gl_captures']['files'] or
            a['vunit_original_mirror']['result']['sha256']!=s['vunit_original_mirror']['result']['sha256'] or
            not p['baseline_qualified'] or p['source_kind']!='scene-boundary Lua read tap'):
        raise ValueError('source-time control and candidate are not qualified')
    am=a['vunit_original_mirror']['result'];bm=b['vunit_original_mirror']['result']
    frame,page=am['frame'],am['visible_page']
    source_frame=am['host_completion']['visible']['frame']
    if (frame!=bm['frame'] or page!=bm['visible_page'] or
            source_frame!=bm['host_completion']['visible']['frame'] or
            source_frame!=p['source_frame']):
        raise ValueError('visible source/page differs')
    texture=source/'run'/f'world-source-{source_frame}-textures.bin'
    if sha(texture)!=sha(source/'run/capture/textureram.bin'):
        raise ValueError('source texture changed before completed capture')
    old_path=control/'run/vunit-fade-producer.bin'
    new_path=trial/'run/vunit-fade-producer.bin'
    old,new=packets(old_path),packets(new_path)
    old_header,old_scene=native_scene(native_control)
    new_header,new_scene=native_scene(native_trial)
    if (old_header!=new_header or len(old)!=len(old_scene) or len(new)!=len(new_scene)
            or any(quad!=row[4:20] for (quad,_),row in zip(old,old_scene))
            or any(quad!=row[4:20] for (quad,_),row in zip(new,new_scene))):
        raise ValueError('source native scenes differ from exact live ordered packets')
    if (any(policy==2 for _,policy in old) or
            any(policy not in (0,1,2) for _,policy in new) or
            [record for record in new if record[1]!=2]!=old):
        raise ValueError('prior packet order or fade policy changed')
    added=[quad for quad,policy in new if policy==2]
    added_scene=[row for (_,policy),row in zip(new,new_scene) if policy==2]
    if (not added or
            any(row[0]&0xc0000000!=0xc0000000 for row in added_scene)):
        raise ValueError('previous packets not retained or no new packets')
    old_paths,aa=planes(control,frame,page)
    new_paths,bb=planes(trial,frame,page)
    if not all(np.array_equal(x,y) for x,y in zip(aa[2:],bb[2:])):
        raise ValueError('original-only indexed planes changed')
    if not all(np.array_equal(x[:,344:2392],y[:,344:2392]) for x,y in zip(aa[:2],bb[:2])):
        raise ValueError('original 4:3 indexed center changed')
    texture_bytes=texture.read_bytes()
    index,tags=render_quads(added,texture_bytes)
    ids,idtags=render_quads(added,texture_bytes,debug_quad_id=True)
    if not np.array_equal(tags!=0,idtags!=0):
        raise ValueError('debug quad IDs changed isolated raster coverage')
    changed=(aa[0]!=bb[0])|(aa[1]!=bb[1])
    covered=tags!=0
    prior=changed & (aa[1]!=0)
    fresh=changed & (aa[1]==0) & (bb[1]!=0)
    ys,xs=np.where(changed)
    qualified_hits={tuple(h['quad_words']):h['object'] for region in p['probes']
                    for h in region['projected_box_hits']
                    if h['stock_horizontal_rejected'] and not h['exact_original_dma']
                    and not h['exact_host_packet']}
    matched=[{'object':qualified_hits[q],'quad_sha256':hashlib.sha256(
        np.asarray(q,dtype='<u2').tobytes()).hexdigest()} for q in added if q in qualified_hits]
    qualified=[q for q in added if q in qualified_hits]
    qindex,qtags=render_quads(qualified,texture.read_bytes()) if qualified else (
        np.zeros_like(index),np.zeros_like(tags))
    qcovered=qtags!=0
    seen_ids,seen_counts=np.unique(ids[changed & covered],return_counts=True)
    attribution=[{'added_packet_ordinal':int(i),'changed_pixels':int(n),
                  'native_object_id':hex(added_scene[int(i)][0]),
                  'source_qualified_roi_object':qualified_hits.get(added[int(i)]),
                  'quad_sha256':hashlib.sha256(np.asarray(added[int(i)],dtype='<u2').tobytes()).hexdigest()}
                 for i,n in zip(seen_ids,seen_counts)]
    attribution.sort(key=lambda row:row['changed_pixels'],reverse=True)
    by_object=Counter()
    for row in attribution:
        by_object[row['native_object_id']]+=row['changed_pixels']
    all_covered=int((changed&covered).sum())==int(changed.sum())
    all_indices_equal=int((changed&covered&(bb[0]==index)).sum())==int(changed.sum())
    return {'passed':bool(changed.any() and all_covered and all_indices_equal),
            'scope':'Exact native source-scene/live-packet join and isolated added-quad raster '
                    'at one completed World frame. No full ordered compositing or temporal acceptance.',
            'source_frame':source_frame,'completed_frame':frame,'visible_page':page,
            'control_packets':len(old),'trial_packets':len(new),'added_packets':len(added),
            'native_scene_packet_order_exact':True,
            'added_packets_all_active_objects':True,
            'source_qualified_roi_added_packets':matched,
            'changed_indexed_pixels':int(changed.sum()),
            'changed_prior_host_owned_pixels':int(prior.sum()),
            'changed_newly_owned_pixels':int(fresh.sum()),
            'changed_pixels_inside_isolated_added_coverage':int((changed&covered).sum()),
            'changed_pixels_outside_isolated_added_coverage':int((changed&~covered).sum()),
            'prior_host_changes_inside_isolated_added_coverage':int((prior&covered).sum()),
            'candidate_index_equal_isolated_on_covered_changes':int((changed&covered&(bb[0]==index)).sum()),
            'changed_pixels_inside_source_qualified_roi_quads':int((changed&qcovered).sum()),
            'changed_pixels_outside_source_qualified_roi_quads':int((changed&~qcovered).sum()),
            'candidate_index_equal_source_qualified_on_covered_changes':int((
                changed&qcovered&(bb[0]==qindex)).sum()),
            'visible_added_packet_attribution':attribution,
            'visible_active_object_attribution':[
                {'native_object_id':object_id,'changed_pixels':pixels}
                for object_id,pixels in by_object.most_common()],
            'changed_bounds':([int(xs.min()),int(ys.min()),int(xs.max()),int(ys.max())] if len(xs) else None),
            'sha256':{'control_report':sha(control/'report.json'),'trial_report':sha(trial/'report.json'),
                      'source_report':sha(source/'report.json'),'projection':sha(projection),
                      'control_packets':sha(old_path),'trial_packets':sha(new_path),
                      'source_texture':sha(texture),
                      'native_control':sha(native_control),'native_trial':sha(native_trial),
                      **{f'control_{q.name}':sha(q) for q in old_paths},
                      **{f'trial_{q.name}':sha(q) for q in new_paths}}}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    for name in ('control','trial','source','projection','native-control','native-trial','report'):
        ap.add_argument('--'+name,type=Path,required=True)
    args=ap.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite overlap evidence')
    result=screen(args.control,args.trial,args.source,args.projection,
                  args.native_control,args.native_trial)
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('PASS' if result['passed'] else 'FAIL',result['added_packets'],
          result['changed_pixels_inside_isolated_added_coverage'],
          result['changed_pixels_outside_isolated_added_coverage'])
    if not result['passed']:
        raise SystemExit(1)


if __name__=='__main__':
    main()
