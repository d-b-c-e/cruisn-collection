"""Offline host drawing of World's pending scenery, with unchanged guest draws.

Diagnostic only: insertion before the main-object pass is a conservative painter
order experiment, not general occlusion acceptance. No guest activation or writes.
"""
import argparse
import collections
import csv
import json
from pathlib import Path
import shutil
import struct

from scenery_c31 import F, signed
from world_host_scenery import camera_center, rotation_matrix, project, fast_quads
from verify_world_transform import DMA_KEYS, verify
from verification import sha256_file, write_json


def preview(run, output):
    if not verify(run)['passed']:
        raise ValueError('host transform prerequisite failed')
    output.mkdir(parents=True, exist_ok=False)
    capture = run/'capture'
    raw = (capture/'quads.bin').read_bytes()
    if raw[:4] != b'MVQ1' or (len(raw)-4) % 38:
        raise ValueError('invalid quad capture')
    all_quads = list(struct.iter_unpack('<IH16H', raw[4:]))
    boundaries = [0]+[i for i in range(1,len(all_quads)) if all_quads[i][1]!=all_quads[i-1][1]]+[len(all_quads)]
    if len(boundaries) < 3:
        raise ValueError('no completed scene')
    start, end = boundaries[-3:-1]
    original = all_quads[start:end]
    page = original[0][1]
    frame = max(q[0] for q in original)
    pending = [json.loads(x) for x in (run/'world-pending-models.jsonl').read_text().splitlines()]
    pending = [r for r in pending if r['frame']==frame and r['page']==page]
    if not pending or len({r['object'] for r in pending}) != len(pending):
        raise ValueError('missing or ambiguous pending scene/LOD')
    recip = dict(zip(range(-80,5000), struct.unpack('<5080I',(run/'world-transform-reciprocals.bin').read_bytes())))
    guest = [json.loads(x) for x in (run/'world-transform.jsonl').read_text().splitlines()]
    guest = [r for r in guest if r['frame']==frame and r['page']==page]
    if {r['object'] for r in guest} & {r['object'] for r in pending}:
        raise ValueError('pending object already present in main draw list')
    # Locate the first main polygon trigger as an ordered trace subsequence.
    traced = [row for row in csv.DictReader((run/'world-transform-draws.csv').open())
              if int(row['frame'])==frame and int(row['page'])==page]
    trace_dmas = [tuple(int(row[k]) for k in DMA_KEYS) for row in traced]
    cursor = 0
    matched = []
    for dma in trace_dmas:
        while cursor < len(original) and tuple(original[cursor][2:17]) != dma:
            cursor += 1
        if cursor == len(original):
            raise ValueError('main draw trace does not match captured scene in order')
        matched.append(cursor)
        cursor += 1
    if not matched:
        raise ValueError('no main object pass anchor')
    insertion = matched[0]
    additions = []
    counts = collections.Counter()
    entries = []
    for r in pending:
        counts['pending_objects'] += 1
        if 'model_words' not in r:
            counts['alternate_codec_excluded'] += 1
            continue
        center = camera_center(r['object_words'], r['camera'], r['view'])
        # This first intervention changes ONLY admission. Preserve the original
        # whole-object distance interval and reject anything needing clipping.
        radius = r['model_words'][0]
        depth = center[2].fix()
        if depth-radius < 1000 or depth+radius >= 80000:
            counts['distance_or_clipping_excluded'] += 1
            continue
        matrix = (r['billboard'] if r['object_words'][14]&8 else
                  [x.store() for x in rotation_matrix(r['object_words'], r['view'])])
        record = dict(r, fast=1, end_pc=0x242, matrix=matrix,
                      camera_space=[x.store() for x in center]+r['origin'])
        projected = project(record, recip)
        quads = fast_quads(record, projected)
        counts['decoded_objects'] += 1
        # Keep the source material/UV/texture selectors; visibility is measured
        # after rasterization rather than inferred from model admission alone.
        additions.append((depth, r['object'], quads))
        entries.append(dict(object=r['object'],model=r['model'],depth=depth,
                            quads=len(quads),section=r['object_words'][27]&65535,
                            guest_threshold=r['pending_threshold']))
    additions.sort(key=lambda x:(-x[0], x[1]))
    added_records = [(frame,page,*q,0) for _,_,quads in additions for q in quads]
    candidate = original[:insertion]+added_records+original[insertion:]
    # The identity and order of every old DMA record are preserved by construction
    # and explicitly checked. This is not proof of correct new occlusion.
    restored = candidate[:insertion]+candidate[insertion+len(added_records):]
    if restored != original or not added_records:
        raise ValueError('original-scene preservation or nonempty extension failed')
    changed = all_quads[:start]+candidate+all_quads[end:]
    dest = output/'capture'
    dest.mkdir()
    for name in ('meta.txt','textureram.bin','paletteram.bin','videoram.bin'):
        shutil.copy2(capture/name, dest/name)
    (dest/'quads.bin').write_bytes(b'MVQ1'+b''.join(struct.pack('<IH16H',*r) for r in changed))
    report = dict(schema=1,passed=True,scope='offline pending-scene construction only',
                  frame=frame,page=page,insertion=insertion,original_quads=len(original),
                  added_quads=len(added_records),counts=dict(counts),objects=entries,
                  original_dma_preserved=True,guest_execution_modified=False,
                  input_hashes={name:sha256_file(run/name) for name in
                                ('world-pending-models.jsonl','world-transform.jsonl','world-transform-draws.csv')},
                  resources={name:sha256_file(dest/name) for name in ('textureram.bin','paletteram.bin')},
                  capture_hashes={'original':sha256_file(capture/'quads.bin'),'extended':sha256_file(dest/'quads.bin')},
                  limitations=['No native host draw implementation',
                    'Original far limit; alternate codecs and near clipping excluded',
                    'Pending RAM resources at one instant; no future section decoder',
                    'Insertion before main-object pass is experimental occlusion ordering'])
    write_json(output/'report.json',report)
    return report


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('run',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=preview(args.run,args.output)
    print(f"Constructed {report['added_quads']} host quads for frame {report['frame']}")


if __name__=='__main__':
    main()
