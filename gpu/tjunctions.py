"""Conservative offline experiment for quantized, materially continuous T joins.

Only a closed A->B, B->P, P->A edge chain across three opaque polygons qualifies.
Position, UV and material form vertex identity. No image-space color filling.
"""
from collections import defaultdict
import numpy as np


def align(quads):
    positions = quads[:, 2:10].copy().view(np.int16).reshape(-1, 4, 2).astype(np.float32)
    edges = defaultdict(list)
    occurrences = defaultdict(list)
    for qi, q in enumerate(quads):
        # Opaque textured only. Preserve transparent sprites, dithering and UI.
        if int(q[0]) & 0x2f00 != 0x100:
            continue
        material = tuple(int(q[k]) for k in (0, 1, 14, 15))
        vertices = [tuple(map(int, positions[qi, v])) + (int(q[10+v]) & 255, int(q[10+v]) >> 8) for v in range(4)]
        for vi, vertex in enumerate(vertices):
            occurrences[(material, vertex)].append((qi, vi))
            nxt = vertices[(vi+1) % 4]
            if vertex[:2] != nxt[:2]:
                edges[(material, vertex)].append((nxt, qi))
    candidates = defaultdict(list)
    for (material, a), outgoing in edges.items():
        for b, qi in outgoing:
            av, bv = np.array(a[:2], dtype=float), np.array(b[:2], dtype=float)
            direction = bv-av
            length2 = float(direction @ direction)
            if length2 < 64:
                continue
            for p, qj in edges.get((material, b), ()):
                if qi == qj or p == a:
                    continue
                closing = [qk for dest, qk in edges.get((material, p), ()) if dest == a and qk not in (qi, qj)]
                if not closing:
                    continue
                pv = np.array(p[:2], dtype=float)
                t = float((pv-av) @ direction) / length2
                if not .01 < t < .99:
                    continue
                target = av + t * direction
                distance = float(np.linalg.norm(target-pv))
                uv = np.array(a[2:]) + t * (np.array(b[2:])-np.array(a[2:]))
                if not .001 < distance <= .75 or np.max(np.abs(uv-np.array(p[2:]))) > .75:
                    continue
                candidates[(material, p)].append(dict(target=target, anchors=(a,b), edge_quad=qi, neighbor_quads=[qj,*closing], distance=distance))
    repairs = []
    for (material, p), choices in candidates.items():
        first = choices[0]
        # Moving an anchor or agreeing with multiple different edges is ambiguous.
        if any((material, anchor) in candidates for c in choices for anchor in c['anchors']):
            continue
        if any(np.linalg.norm(c['target']-first['target']) > .001 for c in choices[1:]):
            continue
        vertices = occurrences[(material, p)]
        for qi, vi in vertices:
            positions[qi, vi] = first['target']
        repairs.append(dict(vertex=list(p), target=first['target'].tolist(), distance=first['distance'],
                            edge_quad=first['edge_quad'], neighbor_quads=first['neighbor_quads'],
                            occurrences=[list(v) for v in vertices], material=list(material)))
    return positions, repairs
