"""Private Exotica Zeus state transitions; no device, FIFO or WaveRAM mutation.

Semantics from MAME zeus2.cpp, BSD-3-Clause, copyright Aaron Giles; full notice in
scenery_c31.py. Material loads are returned as requests, not fulfilled or certified.
Reject unsupported commands atomically. This is a bounded original-state oracle,
not a general Zeus interpreter or an extra-scenery submission path.
"""
import copy
import math
import struct
from exotica_transform import words
from scenery_c31 import F

SCALARS=('quad_size','ucode','palette','texture','yscale','zoffset')
FLOATS=(('matrix',9),('translation',4),('light',3))


def floating(word):
    return struct.unpack('<f',struct.pack('<f',F.load(word).value()))[0]


def validate(context):
    words([context[k] for k in SCALARS],len(SCALARS))
    words(context['regs'],128);words(context['render'],80)
    for key,size in FLOATS:
        if len(context[key])!=size or not all(math.isfinite(v) for v in context[key]):
            raise ValueError('invalid Zeus context transform')
    if context['quad_size'] not in (10,12,14) or context['yscale'] not in (0,1) or context['zoffset']!=0:
        raise ValueError('unsupported Exotica Zeus context')


def _pointer(ctx,value):
    reg=value>>24;v=value&0xffffff
    if reg>=80 or reg==8:raise ValueError('unsupported private render write or model palette load')
    ctx['regs'][0x20]=value;ctx['render'][reg]=v
    if reg in (1,2):ctx['render'][reg]&=0xfff
    if reg==5:ctx['texture']=v%(1024*2048)


def _model(ctx,source):
    words(source,len(source))
    if len(source)%2 or len(source)>2*(0xc800+1):raise ValueError('Zeus model transition budget')
    i=0
    while i<len(source):
        cmd=source[i]>>24;n=ctx['quad_size'] if cmd==0x38 else 2
        d=source[i:i+n];i+=n
        if len(d)!=n:raise ValueError('incomplete model state command')
        ctx['regs'][0x19]=(ctx['regs'][0x19]+n)&0xffffffff
        if cmd in (0,0x22):ctx['regs'][0x68]=(d[0]>>16)&255
        elif cmd==0x36:
            if (d[0]>>16)&127!=0x20:raise ValueError('unsupported private model register')
            _pointer(ctx,d[1])
        elif cmd!=0x38:raise ValueError('unsupported private model command')


def _setup(ctx,source):
    words(source,len(source))
    if not 4<=len(source)<=128:raise ValueError('Zeus setup packet budget')
    i=0;loads=[]
    while i<len(source):
        cmd=source[i]>>24;n={0x32:1,5:2,7:13,0x16:4,0x1c:4}.get(cmd)
        if n is None or i+n>len(source):raise ValueError('unsupported or truncated Zeus setup command')
        data=source[i:i+n];i+=n
        ctx['regs'][0x18]=(ctx['regs'][0x18]+n)&0xffffffff
        if cmd==0x32:continue
        if cmd==7:ctx['matrix']=list(map(floating,data[1:10]));ctx['translation'][:3]=map(floating,data[10:13])
        elif cmd==0x16:ctx['translation'][:3]=map(floating,data[1:])
        elif cmd==0x1c:ctx['light']=list(map(floating,data[1:]))
        else:
            reg=(data[0]>>16)&127;value=data[1]
            if reg not in (0x20,0x40,0x41):raise ValueError('unsupported private setup register')
            ctx['regs'][reg]=value
            if reg==0x20:_pointer(ctx,value)
            elif reg==0x41:ctx['regs'][reg]&=0x1fff03ff
            elif reg==0x40:
                if ctx['regs'][0x4e]&15:raise ValueError('unsupported Zeus load trigger')
                code=(value>>16)&15;address=ctx['regs'][0x41]
                if code==5:
                    # Same Exotica program-layout profiles as MAME's Zeus device.
                    size={0xc0:10,0x136:14,0x22b:12,0x29b:12}.get(address)
                    if value>>24>=0xc0 or size is None:raise ValueError('unsupported Exotica microcode profile')
                    ctx['ucode']=address;ctx['quad_size']=size;ctx['zoffset']=0
                elif code==4:ctx['palette']=address%1024+((address>>16)%2048)*1024
                else:raise ValueError('unsupported Zeus load operation')
                loads.append(dict(kind=code,source=address,control=value))
    return loads


def transition(previous,model,setup,base):
    validate(previous);words([base],1)
    ctx=copy.deepcopy(previous);_model(ctx,model);loads=_setup(ctx,setup)
    # The two model-command words pass through register8 before model dispatch.
    ctx['regs'][0x18]=(ctx['regs'][0x18]+2)&0xffffffff;ctx['regs'][8]=base
    validate(ctx)
    return ctx,loads
