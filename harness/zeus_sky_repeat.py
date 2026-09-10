"""Independent structural panorama repetition; private host copies only.

Requires a single unchanged palette/material lifetime supplied by the caller.
No model IDs, texture-address allowlist, fixed panorama period or stretched UVs.
"""
import numpy as np

def plan(tiles,margin=88):
 if not 8<=len(tiles)<=64 or not 1<=margin<=120:return dict(accepted=False,reason='count',copies=[])
 for q in tiles:
  v=q['verts'][:4]
  if int(q['yscale']) or int(q['rr04']) not in (0,400) or list(q['clip'])!=[0,0,511,399]:return dict(accepted=False,reason='page/clip',copies=[])
  if int(q['rr04'])!=int(tiles[0]['rr04']) or v[0,2]!=tiles[0]['verts'][0,2] or v[0,5]!=tiles[0]['verts'][0,5]:return dict(accepted=False,reason='plane',copies=[])
  if not (v[0,2]>0 and v[0,5]>0 and 1<v[1,0]-v[0,0]<4096 and 1<v[2,1]-v[0,1]<2048):return dict(accepted=False,reason='dimensions',copies=[])
  if int(q['flags'])&~512!=52 or int(q['numverts'])!=4 or not np.isfinite(v).all() or np.max(np.abs(v))>1e12:return dict(accepted=False,reason='flags',copies=[])
  if not np.all(v[:,2]==v[0,2]) or not np.all(v[:,5]==v[0,5]):return dict(accepted=False,reason='coplanar',copies=[])
  if not (abs(v[0,0]-v[3,0])<.002 and abs(v[1,0]-v[2,0])<.002 and abs(v[0,1]-v[1,1])<.002 and abs(v[2,1]-v[3,1])<.002):return dict(accepted=False,reason='rect',copies=[])
 def signature(q):return tuple(int(q[k]) for k in ('texdata','tex_src','texwidth','solidcolor','transcolor','srcAlpha','dstAlpha','flags','zbuf_min','rr04','yscale'))+tuple(q['clip'])+tuple(q['verts'][:4,1:].ravel())
 keys=[signature(q) for q in tiles];bands={}
 def same(i,j):
  a,b=tiles[i]['verts'],tiles[j]['verts']
  return keys[i]==keys[j] and abs(float((a[1,0]-a[0,0])-(b[1,0]-b[0,0])))<.002
 for i,q in enumerate(tiles):
  v=q['verts'][:4];key=(float(v[:,1].min()),float(v[:,1].max()))
  bands.setdefault(key,[]).append(i)
 if len(bands)>4:return dict(accepted=False,reason='bands',copies=[])
 bounds={}
 for band,ids in bands.items():
  ordered=sorted(ids,key=lambda i:float(tiles[i]['verts'][:4,0].min()))
  left=float(tiles[ordered[0]]['verts'][:4,0].min());right=float(tiles[ordered[-1]]['verts'][:4,0].max())
  if left>0 or right<512 or right-left<1024:return dict(accepted=False,reason='extent',copies=[])
  for a,b in zip(ordered,ordered[1:]):
   if abs(float(tiles[a]['verts'][:4,0].max()-tiles[b]['verts'][:4,0].min()))>.02:return dict(accepted=False,reason='gap',copies=[])
  bounds[band]=(left,right)
 deltas=set()
 for i,a in enumerate(tiles):
  for j,b in enumerate(tiles[:i]):
   d=abs(float(a['verts'][0,0]-b['verts'][0,0]))
   if same(i,j) and 512<d<16384:deltas.add(round(d,2))
 if len(deltas)>64:return dict(accepted=False,reason='budget',copies=[])
 period=None;comparisons=0
 for d in sorted(deltas):
  matched=0;failed=False
  for i,a in enumerate(tiles):
   for shift in (-d,d):
    pairs=[j for j,b in enumerate(tiles) if abs(float(b['verts'][0,0]-a['verts'][0,0])-shift)<.02 and abs(float(b['verts'][0,1]-a['verts'][0,1]))<.002]
    if pairs:
     matched+=1
     if len(pairs)!=1 or not same(pairs[0],i):failed=True;break
   if failed:break
  if not failed and matched>=len(tiles):period=d;comparisons=matched;break
 if period is None:return dict(accepted=False,reason='period',copies=[])
 copies=[]
 for band,ids in bands.items():
  if band[1]<=0 or band[0]>=400:continue
  lo,hi=bounds[band]
  for side,needed,target in [('left',lo>-margin,lo),('right',hi<512+margin,hi)]:
   if not needed:continue
   options=[]
   for i in ids:
    v=tiles[i]['verts'][:4];edge=float(v[:,0].max() if side=='left' else v[:,0].min())
    k=round((target-edge)/period)
    if k and abs(edge+k*period-target)<.02:options.append((i,float(np.float32(target-edge))))
   if not options:return dict(accepted=False,reason='missing tile',copies=[])
   i,shift=options[0];q=tiles[i].copy();q['verts'][:4,0]+=np.float32(shift)
   low,high=map(float,(q['verts'][:4,0].min(),q['verts'][:4,0].max()))
   if (side=='left' and (low>-margin or high>0)) or (side=='right' and (high<512+margin or low<512)):return dict(accepted=False,reason='coverage',copies=[])
   copies.append(dict(index=i,shift=shift,side=side))
 return dict(accepted=True,period=period,overlap_comparisons=comparisons,copies=copies)
