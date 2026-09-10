"""Independent read-only Zeus2 packed-model projection and material-state oracle.

Semantics from MAME zeus2.cpp and poly.h, BSD-3-Clause, copyright Aaron Giles.
Full BSD notice: scenery_c31.py. Context register writes are applied to private
copies. Palette loads require a separately verified live-material contract.
No game model, program or texture operands are included.
"""
import collections
import struct
import math
import numpy as np
from scenery_c31 import signed

F=np.float32
def float_word(w):return struct.unpack('<f',struct.pack('<I',w))[0]
def project(d,tex,regs,matrix,trans):
 xyz=[[signed(d[2],16),signed(d[3],16),signed(d[6],16)],
      [signed(d[2]>>16,16),signed(d[3]>>16,16),signed(d[6]>>16,16)],
      [signed(d[8],16),signed(d[9],16),signed(d[7],16)],
      [signed(d[8]>>16,16),signed(d[9]>>16,16),signed(d[7]>>16,16)]]
 uv=[(d[1]&1023,(d[1]>>16)&1023),(d[4]&1023,(d[4]>>10)&1023),((d[4]>>20)&1023,d[5]&1023),((d[5]>>10)&1023,(d[5]>>20)&1023)]
 if not -31<=regs[0x66]-0x8e<=31 or not -31<=regs[0x68]-0x9d<=31 or not 0<=regs[0x6c]<=30:raise ValueError('Zeus projection exponent')
 scale=F(2.**(regs[0x66]-0x8e));uvscale=F(2.**(regs[0x68]-0x9d))
 verts=[]
 for (x,y,z),(u,v) in zip(xyz,uv):
  x,y,z=[F(F(n)*scale) for n in (x,y,z)]
  position=[F(F(F(F(x*m[0])+F(y*m[1]))+F(z*m[2]))+trans[j]) for j,m in enumerate(matrix)]
  verts.append(np.array([*position,F(F(F(u)*uvscale)*F(256)),F(F(F(F(v)*uvscale)+F(tex>>16))*F(256)),F(0)],dtype=F))
 if not all(math.isfinite(float_word(regs[i])) for i in (0x78,0x6a,0x6b)):raise ValueError('nonfinite Zeus projection register')
 clip=F(float_word(regs[0x78]));clipped=[];prev=verts[-1];prior=prev[2]<clip
 for v in verts:
  outside=v[2]<clip
  if outside!=prior:
   fraction=F(F(clip-prev[2])/F(v[2]-prev[2]));clipped.append(np.array([F(a+F(fraction*F(b-a))) for a,b in zip(prev,v)],dtype=F))
  if not outside:clipped.append(v.copy())
  prior=outside;prev=v
 if len(clipped)<3:return None,'near'
 for v in clipped:
  if v[2]<0:v[2]=F(0)
  ooz=F(F(1<<regs[0x6c])/F(v[2]+F(2)))
  v[0]=F(F(v[0]*ooz)+F(float_word(regs[0x6a])))
  v[1]=F(F(v[1]*ooz)+F(float_word(regs[0x6b])))
  v[2]=F(v[2]*F(4096));v[3]=F(v[3]*ooz);v[4]=F(v[4]*ooz);v[5]=ooz
  if not np.all(np.isfinite(v)):raise ValueError('nonfinite Zeus projected vertex')
 a,b,c=clipped[:3]
 hsr=F(F(F(a[1]-b[1])*F(b[0]-c[0]))-F(F(a[0]-b[0])*F(b[1]-c[1])))
 if hsr>=0:return None,'backface'
 return np.array(clipped,dtype=F),'draw'

def decode(r):
 if r['quad_size'] not in (10,12,14) or len(r['words'])%2 or len(r['words'])>2*(0xc800+1):raise ValueError('Zeus model bounds')
 for key,length in (('regs',128),('render',80),('words',len(r['words']))):
  if len(r[key])!=length or any(type(w) is not int or not 0<=w<=0xffffffff for w in r[key]):raise ValueError('Zeus context words')
 if len(r['matrix'])!=9 or len(r['translation'])<3 or not all(math.isfinite(x) for x in r['matrix']+r['translation']):raise ValueError('Zeus matrix bounds')
 regs=r['regs'].copy();render=r['render'].copy();tex=0;texture=r['texture'];i=0
 matrix=np.array(r['matrix'],dtype=F).reshape((3,3));trans=np.array(r['translation'][:3],dtype=F)
 result=[];stats=collections.Counter();raw=r['words']
 while i<len(raw):
  cmd=raw[i]>>24;size=r['quad_size'] if cmd==0x38 else 2
  if i+size>len(raw):raise ValueError(f'incomplete model offset{i} cmd{cmd:x}')
  d=raw[i:i+size];i+=size;stats['cmd'+hex(cmd)]+=1
  if cmd in (0,0x22):regs[0x68]=(d[0]>>16)&255;tex=d[1]
  elif cmd==0x36:
   register=(d[0]>>16)&127;regs[register]=d[1]
   if register!=0x20:raise ValueError('unsupported model register '+hex(register))
   pointer,value=d[1]>>24,d[1]&0xffffff
   if pointer>=80:raise ValueError('unsupported render register '+hex(pointer))
   render[pointer]=value;stats['render'+hex(pointer)]+=1
   if pointer==5:texture=value%(1024*2048)
   if pointer in (1,2):render[pointer]&=0xfff
   if pointer==8:raise ValueError('model palette load requires live material binding')
  elif cmd==0x38:
   points,kind=project(d,tex,regs,matrix,trans);stats[kind]+=1
   if points is None:continue
   mode=tex&65535;typ=mode&3;alpha=typ==2 and bool(mode&0x80)
   flags=(1 if mode&0xc00==0xc00 else 0)|(2 if render[0x40]==0x20202 or render[0x40]==0x21e0e and typ==2 else 0)|4
   if not render[0x14]&0x20 and not alpha:flags|=8
   if not render[0x14]&0x1000 and not alpha:flags|=16
   if render[0x14]&0xc00:flags|=32
   if alpha:flags|=64
   if typ==2 and not alpha:flags|=128
   width=0x20<<((mode>>2)&3)
   if typ==0:width>>=1
   fields=[r['frame'],len(points),tex,texture,width,regs[0]&0x7fff,0 if mode&0x180 else 0x100,
    min(render[0xc],0x100),min(render[0xd],0x100),flags,signed(render[0x15],24)&0xffffffff,render[4],r['yscale'],0,0,render[1]&0xfff,render[2]&0xfff]
   result.append((fields,points))
  else:raise ValueError('unsupported model command '+hex(cmd))
 return result,stats

