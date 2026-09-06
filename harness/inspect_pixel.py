"""Report current-scene primitive ownership around a recorded GPU buffer pixel."""
import argparse
from pathlib import Path
import numpy as np
from verification import sha256_file, write_json


def inspect(path, x, y, radius=4):
    with np.load(path, allow_pickle=False) as data:
        owners, indices, coverage, quads = (data[k] for k in ('owners','indices','coverage','quads'))
        if owners.ndim != 2 or indices.shape != owners.shape or coverage.shape != owners.shape:
            raise ValueError('inconsistent buffer shapes')
        if not 0 <= x < owners.shape[1] or not 0 <= y < owners.shape[0] or not 0 <= radius <= 64:
            raise ValueError('pixel/radius is outside the buffer or diagnostic budget')
        ids, counts = np.unique(owners[max(0,y-radius):y+radius+1,max(0,x-radius):x+radius+1],return_counts=True)
        neighbors = []
        for owner,count in zip(ids,counts):
            item = {'owner':int(owner),'pixels':int(count)}
            if owner!=65535:
                if owner>=len(quads): raise ValueError('owner does not name a captured polygon')
                q=quads[owner]
                item.update(dma=[int(v) for v in q], xy=q[2:10].copy().view(np.int16).reshape(4,2).tolist(),
                            uv=[[int(v)&255,int(v)>>8] for v in q[10:14]],
                            texture_base_bytes=int(q[14])*256, palette_base=int(q[1]),flags=int(q[0]))
                if 'positions' in data: item['quality_xy']=data['positions'][owner].tolist()
            neighbors.append(item)
        return {'schema':1,'scope':'offline current-scene ownership; 65535 means no current owner',
                'buffers_sha256':sha256_file(path),'pixel':[x,y], 'radius':radius,
                'index':int(indices[y,x]),'owner':int(owners[y,x]),'covered':bool(coverage[y,x]),
                'scale':int(data['scale']),'margin':int(data['margin']),'neighbors':neighbors}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('buffers',type=Path)
    ap.add_argument('x',type=int);ap.add_argument('y',type=int)
    ap.add_argument('--radius',type=int,default=4);ap.add_argument('--report',required=True)
    args=ap.parse_args()
    write_json(args.report,inspect(args.buffers,args.x,args.y,args.radius))
    print(args.report)


if __name__=='__main__': main()
