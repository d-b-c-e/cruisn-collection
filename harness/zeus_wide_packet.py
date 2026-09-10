"""Independent bounded XWD1 decoder. Raw game resources remain local."""
import math
import struct
from zeus_host_materials import MAX_PACKET as MAX_MATERIAL, parse as parse_material

HEADER=struct.Struct('<8I')
QUAD=struct.Struct('<18I48f')
MAX_QUADS=131072
MAX_DEPTH=67108860
MAX_PACKET=HEADER.size+MAX_MATERIAL+MAX_QUADS*QUAD.size


def validate_quad(state, vertices, frame, page):
    if (len(state)!=17 or len(vertices)!=8 or state[0]!=frame or not 3<=state[1]<=8
            or page not in (0,400) or state[11]!=page or state[12] or state[13]!=0
            or state[15]!=511 or not 0<=state[14]<=state[16]<=399
            or not state[9]&8 or state[9]&~0x2df or state[7]>256 or state[8]>256):
        raise ValueError('wide geometry state/frame/page/flags')
    bias=state[10] if state[10]<0x80000000 else state[10]-0x100000000
    for v in vertices[:state[1]]:
        if len(v)!=6 or not all(math.isfinite(x) for x in v) or v[5]<=0 or not 0<=v[2]<=MAX_DEPTH:
            raise ValueError('wide geometry finite/perspective/depth bounds')
        endpoints=(math.floor(v[2]),math.ceil(v[2]))
        for endpoint in endpoints:
            if state[9]&4:depth=max(endpoint,bias) if state[9]&512 else endpoint+bias
            else:depth=endpoint
            if not 0<=depth<=MAX_DEPTH:
                raise ValueError('wide geometry biased depth bounds')


def parse(wire):
    if not HEADER.size<=len(wire)<=MAX_PACKET:
        raise ValueError('wide packet length')
    magic,material_size,count,margin,page,multiplier,draw,reserved=HEADER.unpack_from(wire)
    if (magic!=0x31445758 or not 96<=material_size<=MAX_MATERIAL or count>MAX_QUADS
            or margin>120 or page not in (0,400) or multiplier not in (1,2,3)
            or draw not in (0,1) or reserved
            or len(wire)!=HEADER.size+material_size+count*QUAD.size):
        raise ValueError('wide packet header')
    materials=parse_material(wire[HEADER.size:HEADER.size+material_size])
    quads=[]
    for values in QUAD.iter_unpack(wire[HEADER.size+material_size:]):
        palette=values[0];state=values[1:18];flat=values[18:]
        vertices=tuple(tuple(flat[i:i+6]) for i in range(0,48,6))
        if palette>=len(materials['palettes']):
            raise ValueError('wide private palette index')
        validate_quad(state,vertices,materials['frame'],page)
        quads.append(dict(palette=palette,state=state,vertices=vertices))
    return dict(materials=materials,margin=margin,page=page,multiplier=multiplier,draw=bool(draw),quads=quads)
