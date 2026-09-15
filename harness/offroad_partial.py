"""Independent optional recovery of unallocated ordinary partial-frontier sources."""
from offroad_sections import frontier, descriptor, span
from verify_offroad_future import allocated_pool


def recover(read, result):
    f = result['frontier']
    if f['pretrack'] or not f['partial'] or f['front']+1 >= f['count']:
        return result
    if frontier(read) != f or read(0x111f6) != 0x1b754:
        raise ValueError('partial recovery frontier/free-list guard')
    tags = allocated_pool(read)
    number = f['front']+1; entry = f['track']+4*number; data = read(entry+3)
    if not span(data,17):
        raise ValueError('partial section header')
    count = read(data+16)
    if not 1 <= count <= 256 or not span(data+17,11*count) or len(result['sources'])+count > 32768:
        raise ValueError('partial section source budget')
    binding = [read(p) for p in (0x1b4cd,0x1b4cf,0x1b4ce)]
    existing = {s['source'] for s in result['sources']}; extra = []
    for ordinal in range(count):
        source = data+17+11*ordinal; definition = [read(source+i) for i in range(11)]
        obj = descriptor(definition,number,ordinal,count,binding)
        if obj is None or obj[5]&0x200e or tags.get(obj[6]):
            continue
        if source in existing:
            raise ValueError('partial source already enumerated')
        extra.append(dict(entry=entry,source=source,number=number,ordinal=ordinal,
                          flags=definition[0],supported=True,words=obj,definition=definition))
    return dict(result,sources=extra+result['sources'])
