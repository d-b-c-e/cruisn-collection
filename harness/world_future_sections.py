"""World 2.4 section descriptors without guest allocation or per-model rules.

This is a diagnostic reference. Custom allocation remains excluded; resource
lookup validity is not evidence that the GPU slot still contains the right data.
"""
from scenery_c31 import F,signed
from verify_world_sections import placement,yaw_matrix


def rom_span(p,n):
    return isinstance(p,int) and 0xc00000<=p and 0<=n<=65536 and p+n<=0x1000000


def flags(metadata):
    kind=(metadata>>8)&15
    return 0x2000 | ((metadata>>16)&15) | int(bool(metadata&0xf000)) | {
        3:1<<21,9:1<<21,6:1<<31,7:1<<22}.get(kind,0)


def descriptor(row,*,roads=False):
    """Reconstruct fields consumed by packed scenery from captured operands.

    Class A custom allocation stays excluded. Explicit roads=True adds class B
    render fields, without reproducing physics links or guest allocations.
    """
    definition=row['definition']
    if len(definition)!=6 or len(row['binding_resources'])!=6:
        raise ValueError('incomplete section descriptor operands')
    metadata=definition[5]
    kind=(metadata>>8)&15
    if kind==10 or (kind==11 and not roads):return None
    obj=[0]*28
    obj[1:4],obj[20]=placement(row)
    obj[4:13]=yaw_matrix(F.load(definition[4])+F.load(row['heading']),row['trig_constants'])
    obj[13]=definition[0];obj[14]=flags(metadata);obj[15]=metadata&65535
    if kind==11:
        obj[14]|=1<<28
        obj[15]=(metadata&0xf000)|0x300
    obj[16:18]=row['binding_resources'][4:6]
    index=signed(metadata)>>20
    if index!=row['override_index']:raise ValueError('metadata override index mismatch')
    if index>=0 and 0<=row['override_lookup']<0x80000000:obj[16]=row['override_lookup']
    obj[27]=row['section_tag']
    if kind==11:obj[27]|=(1<<24)|((1<<25) if row['section_flags']&16 else 0)
    return obj


def section_definitions(read,p):
    if not rom_span(p,8):raise ValueError('section header outside ROM')
    section=[read(p+i) for i in range(8)]
    extra=4 if section[0]&8 else 0
    if not rom_span(p,8+extra):raise ValueError('section offset outside ROM')
    section += [read(p+8+i) for i in range(extra)]
    definitions=[]
    for slot in (5,6,7):
        block=section[slot]
        if not block:continue
        if not rom_span(block,2):raise ValueError('section list outside ROM')
        header=read(block+1);count=header&65535
        if not 0<count<=4096 or not rom_span(block+2,6*count):
            raise ValueError('unsupported section list length')
        for index in range(count):
            source=block+2+6*index
            definitions.append(dict(section_pointer=p,section_words=section,source=source,list_slot=slot,
                ordinal=index,definition=[read(source+i) for i in range(6)],
                section_flags=section[0]&~8 if slot==7 else section[0],heading=section[4]))
    return definitions,p+8+extra


def material_operands(read,definition):
    model=definition[0]
    if not rom_span(model-2,5):raise ValueError('model header outside ROM')
    pi,ti=read(model-2),read(model-1)
    pt,tt=read(0x4151),read(0x4150)
    pa,ta=pt+pi,tt+ti
    # Fail closed on signed/missing indices; never alias arithmetic into I/O.
    if not (0<=pt<0x20000 and 0<=tt<0x20000 and 0<=pa<0x20000 and 0<=ta<0x20000):
        raise ValueError('material lookup outside main RAM')
    resources=[pi,ti,pt,tt,read(pa),read(ta)]
    index=signed(definition[5])>>20
    override=-1
    if index>=0:
        if pt+index>=0x20000:raise ValueError('palette override outside main RAM')
        override=read(pt+index)
    return resources,index,override


def future(read,sections=64):
    """Enumerate not-yet-allocated definitions from the saved loader frontier.

    The current partial section uses the guest's list stage and next-definition
    cursor. Later sections remain entirely host-owned. No guest state is written.
    """
    if not 1<=sections<=128:raise ValueError('bounded section count required')
    start=read(0xd575);stage=read(0xd5a5);cursor=read(0xd5a1)
    if stage not in (0,1,2):raise ValueError('unsupported loader stage')
    result=[];p=start;stop=None;skipped=0
    for number in range(sections):
        if rom_span(p,1) and read(p)==0xffffffff:
            stop=dict(section=p,reason='end marker');break
        try:definitions,next_section=section_definitions(read,p)
        except ValueError as error:
            if number==0:raise
            stop=dict(section=p,reason=str(error));break
        if not definitions:
            stop=dict(section=p,reason='section has no object lists');break
        if number==0 and stage:
            active_slot=4+stage
            active=[r for r in definitions if r['list_slot']==active_slot]
            # One-past-end can remain saved while the stage advances next call.
            boundaries={r['source'] for r in active}|({active[-1]['source']+6} if active else set())
            if cursor not in boundaries:raise ValueError('partial section cursor is outside its active list')
        for row in definitions:
            if number==0 and stage and (row['list_slot']<4+stage or
                row['list_slot']==4+stage and row['source']<cursor):
                skipped+=1;continue
            row['relative_section']=number
            result.append(row)
        p=next_section
    return dict(start=start,stage=stage,cursor=cursor,definitions=result,skipped_allocated=skipped,stop=stop)
