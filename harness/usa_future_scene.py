"""Independent USA cached-source admission/material contract, without a cache."""
from collections import Counter
from usa_sections import future, final_flags, material_operands, placement, palette_ownership


def uploads(read):
    p = read(0xcc3f); seen = set(); banks = set(); texture = False
    while p:
        if not 0xcc42 <= p < 0xce42 or (p-0xcc42) % 4 or p in seen or len(seen) >= 128:
            raise ValueError('invalid USA upload queue')
        seen.add(p)
        destination, length = read(p+2), read(p+3) & 0x7fffffff
        if not 1 <= length <= 0x200000:
            raise ValueError('invalid USA upload extent')
        end = destination+length
        if 0x9e0000 <= destination < end <= 0x9e8000:
            banks.update(range((destination-0x9e0000)//256, (end-1-0x9e0000)//256+1))
        elif 0xa00000 <= destination < end <= 0xc00000:
            texture = True
        else:
            raise ValueError('unmapped USA upload target')
        p = read(p)
    return len(seen), banks, texture


def collect(read):
    result = future(read)
    counts = dict(sections=len({r['section_pointer'] for r in result['definitions']}),
                  definitions=len(result['definitions']), special=0, unbound=0, deferred=0, ready=0, uploads=0)
    if result['stop'] == 'track not initialized':
        return result, counts, []
    count, held_banks, texture_hold = uploads(read); counts['uploads'] = count
    if read(0x62) != read(0x9ea9):
        raise ValueError('USA palette tables disagree')
    objects, ordinals = [], Counter()
    for row in result['definitions']:
        section = row['section_pointer']; ordinal = ordinals[section]; ordinals[section] += 1
        meta, model = row['definition'][5], row['definition'][0]
        if meta & 0x2000:
            counts['special'] += 1; continue
        operand = dict(row, trig_constants=[read(0xc8ed+i) for i in range(7)], **material_operands(read, model))
        flags = final_flags(operand['model_prefix'], meta)
        if flags & 0x8e3:
            counts['special'] += 1; continue
        indices = {operand['model_prefix'] & 0xfff}
        if not flags & 0x400:
            header = read(model+1); vertices, polygons = (header & 255)+1, (header >> 16)+1
            if polygons > 1024 or model+2+2*vertices+5*polygons > 0x1000000:
                raise ValueError('invalid future material model bounds')
            indices.update(read(model+2+2*vertices+5*i) >> 16 for i in range(polygons))
        slots, unbound = {}, False
        for index in indices:
            try:
                slot = palette_ownership(read, index)
            except ValueError as error:
                if 'current slot owner' not in str(error): raise
                slot = None
            if slot is None: unbound = True
            else: slots[index] = slot
        if unbound:
            counts['unbound'] += 1; continue
        if texture_hold or held_banks.intersection(slots.values()):
            counts['deferred'] += 1; continue
        obj = [0]*32
        obj[1:4], obj[21], obj[4:13] = placement(operand)
        obj[13], obj[14] = model, flags | 0x2000
        obj[15] = 0x300 if (meta >> 8) & 15 == 11 else meta & 0xfff
        obj[16] = slots[operand['model_prefix'] & 0xfff] << 8
        obj[31] = row['section_number'] << 8 | 0xaa
        if (meta >> 8) & 15 == 11:
            obj[30] = row['section_number'] << 8 | (255-(meta & 255) if row['section_flags'] & 8 else meta & 255)
        if len(objects) >= 16384 or ordinal >= 65536 or row['section_number'] >= 32768:
            raise ValueError('USA future descriptor/identity limit')
        objects.append((0x80000000 | row['section_number'] << 16 | ordinal, obj)); counts['ready'] += 1
    return result, counts, objects
