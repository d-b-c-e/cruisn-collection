"""Compare first host submissions of screenshot-attributed USA bridge objects.

Streams the two existing detailed traces once. Source admission is distinct
from visible completed pixels and cannot prove a smooth or complete bridge.
"""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path

from screen_vunit_panorama_strips import sha


def census(path, ids, expected_hash):
    digest = hashlib.sha256()
    scenes = defaultdict(lambda: dict(packets=0, depth_min=1 << 31, depth_max=0))
    with path.open('rb') as stream:
        header = stream.readline()
        digest.update(header)
        if header.strip().split(b',')[:6] != \
                [b'frame', b'time', b'page', b'object', b'model', b'depth']:
            raise ValueError('unexpected detailed USA quad schema')
        for line in stream:
            digest.update(line)
            fields = line.split(b',', 6)
            object_id = int(fields[3])
            if object_id not in ids:
                continue
            frame, page, depth = int(fields[0]), int(fields[2]), int(fields[5])
            row = scenes[(object_id, frame, page)]
            row['packets'] += 1
            row['depth_min'] = min(row['depth_min'], depth)
            row['depth_max'] = max(row['depth_max'], depth)
    if digest.hexdigest() != expected_hash:
        raise ValueError('detailed trace changed since pixel/activation screen')
    return scenes


def screen(control, candidate, pixel_path, activation_path):
    pixel = json.loads(pixel_path.read_text(encoding='utf-8'))
    activation = json.loads(activation_path.read_text(encoding='utf-8'))
    a = json.loads((control / 'report.json').read_text(encoding='utf-8'))
    b = json.loads((candidate / 'report.json').read_text(encoding='utf-8'))
    if (not pixel['passed'] or not activation['passed'] or
            not a['passed'] or not b['passed'] or
            a['case'] != b['case'] or
            a['emulator_source']['executable_sha256'] !=
            b['emulator_source']['executable_sha256'] or
            activation['sha256']['detailed_replay_report'] != sha(control / 'report.json') or
            pixel['sha256']['detailed_report'] != sha(candidate / 'report.json')):
        raise ValueError('qualified detailed trace or recording identity differs')
    ids = {int(value, 16) for value in pixel['new_packet_samples_by_object']}
    if ids != {0x800a0040, 0x800a0042}:
        raise ValueError('screenshot-attributed member set differs')
    old = census(control / 'run/usa-host-quads.csv', ids,
                 activation['sha256']['detailed_host_quads'])
    new = census(candidate / 'run/usa-host-quads.csv', ids,
                 pixel['sha256']['trace_quads'])
    members = []
    control_through = a['vunit_runtime']['result']['prepared_frame']
    for object_id in sorted(ids):
        def summary(rows, required):
            found = sorted((frame, page, entry) for (obj, frame, page), entry
                           in rows.items() if obj == object_id)
            if not found:
                if required:
                    raise ValueError('candidate member absent from detailed trace')
                return None
            return dict(first_frame=found[0][0], last_frame=found[-1][0],
                        scenes=len(found), packets=sum(item[2]['packets'] for item in found),
                        source_10473_packets=sum(item[2]['packets'] for item in found
                                                 if item[0] == 10473),
                        first_depth_range=[found[0][2]['depth_min'],found[0][2]['depth_max']])
        ordinary, covered = summary(old, False), summary(new, True)
        if ordinary is not None and covered['first_frame'] >= ordinary['first_frame']:
            raise ValueError('candidate did not submit the selected member earlier')
        members.append(dict(object=hex(object_id), ordinary=ordinary,
                            partial_coverage=covered,
                            first_submission_lead_frames=(ordinary['first_frame']-
                                                          covered['first_frame'])
                            if ordinary is not None else None,
                            ordinary_not_seen_through=control_through
                            if ordinary is None else None,
                            lead_strictly_more_than_frames=(control_through-
                                                            covered['first_frame'])
                            if ordinary is None else None,
                            completed_10476_new_red_center_samples=
                                pixel['new_packet_samples_by_object'][hex(object_id)]))
    return dict(schema=1, passed=True,
                scope='Two screenshot-attributed USA future objects on one Golden Gate '
                      'drive. One ordinary member may be unobserved by trace end. '
                      'First source submission is not first visible pixel or '
                      'smooth transition; only completed10476 is packet-attributed.',
                members=members,
                sha256={'pixel_screen': sha(pixel_path), 'activation': sha(activation_path),
                        'control_report': sha(control / 'report.json'),
                        'candidate_report': sha(candidate / 'report.json'),
                        'control_trace': activation['sha256']['detailed_host_quads'],
                        'candidate_trace': pixel['sha256']['trace_quads']})


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ('control', 'candidate', 'pixel', 'activation', 'report'):
        ap.add_argument('--' + name, type=Path, required=True)
    args = ap.parse_args()
    if args.report.exists():
        raise ValueError('refusing to overwrite member-timing screen')
    result = screen(args.control, args.candidate, args.pixel, args.activation)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print('PASS', [(r['object'], r['first_submission_lead_frames'])
                   for r in result['members']])


if __name__ == '__main__':
    main()
