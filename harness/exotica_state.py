"""Independent Exotica 2.4 per-object Zeus setup, without hardware writes.

Reconstructs the game's command packet from explicitly supplied operands and
prior CPU-side caches. This includes inherited state: the light branch does not
reset depth register 0x15. Generating these words is not permission to submit them to the
real Zeus FIFO. A host renderer needs a private context and checked materials.
"""
from exotica_transform import words
from scenery_c31 import F


def setup(obj, flags, cache, constants, commands, programs, bodies, defaults, palette_setup):
    obj,cache=words(obj,32),words(cache,3)
    constants,commands=words(constants,12),words(commands,46)
    programs=words(programs,4)
    if len(bodies)!=4 or not 1<=len(defaults)<=16:
        raise ValueError('invalid Exotica state program/default bounds')
    bodies=[words(body,4) for body in bodies];defaults=words(defaults,len(defaults))
    words([flags,palette_setup],2)
    c=lambda address:constants[address-0x67d0]
    w=lambda address:commands[address-0xb479]
    if (not c(0x67d6) or [w(a) for a in (0xb47b,0xb47c,0xb481,0xb482,0xb493)] !=
            [0x32000000,0x1c000000,0x05410000,0x05400000,0x05200000] or
            any(b[0]!=0x05410000 or b[2]!=0x05400000 for b in bodies)):
        raise ValueError('unsupported Exotica state command layout')
    out=[];branch='cached';selected=-1
    def pointer(value):out.extend([w(0xb493),value])
    key=(flags&c(0x67d2))|(obj[16]&0xffff0000)
    changed=key!=cache[2]
    # 68D2..68D4 execute in the delayed branch even when setup is reused.
    cache[2]=0xffffffff if flags&0x800 else key
    if changed:
        selected=2 if flags&0x8000 else 0
        if flags&0x4000:selected=1
        if flags&c(0x67d6)==c(0x67d6):selected=3
        if programs[selected]!=cache[1]:
            cache[1]=programs[selected];out.extend([w(0xb47b),*bodies[selected]])
        high=obj[16]>>16
        if flags&c(0x67d6)==c(0x67d6):
            branch='light'
            pointer(w(0xb4a1));pointer(w(0xb498));pointer(w(0xb4a6)|((high>>8)<<1))
            out.extend([w(0xb47c),F.integer(10).store(),
                        (-F.integer(5)*F.load(0xff000000)).store(),
                        (F.integer(high&255)*F.load(c(0x67d7))).store()])
        elif flags&0x100:
            branch='fade'
            pointer(w(0xb49d)|0x7ff);pointer(w(0xb4a0))
            pointer(w(0xb4a4)|(high&255));pointer(w(0xb4a6)|((high>>8)<<1))
            pointer(w(0xb499 if flags&8 else 0xb498))
        elif flags&0x400:
            branch='flag400';pointer(c(0x67d3));pointer(w(0xb498))
        elif flags&0x200:
            branch='flag200';pointer(c(0x67d4));pointer(c(0x67d5))
        else:
            branch='default'
            for value in defaults:pointer(value)
            pointer(w(0xb49d))
    if obj[18]!=cache[0]:
        cache[0]=obj[18]
        out.extend([w(0xb47b),w(0xb481),obj[18],w(0xb482),palette_setup])
    return dict(packet=out,cache=cache,branch=branch,program=selected)


def operands(row):
    return (row['object_words'],row['flags'],row['state_cache'][:3],row['state_constants'],
            row['state_commands'],row['programs'],[row['program'+str(i)] for i in range(4)],
            row['default_state'],row['palette_setup'])
