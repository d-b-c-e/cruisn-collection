"""Independent PIM1 reference: reconstruct full owned images from queued pages.

The XOR of indexed FNV-1a page hashes detects accidental corruption, not attacks.
Raw textures and encoded packets are local diagnostic artifacts, never fixtures.
"""
import struct

HEADER = struct.Struct('<4I4Q4I')
MASK = (1 << 64) - 1


def page_hash(index, data):
    value = 14695981039346656037
    for byte in struct.pack('<I', index) + data:
        value = ((value ^ byte) * 1099511628211) & MASK
    return value


class Image:
    def __init__(self, size, page_size):
        if not 0 < size <= 0xffffffff or not 0 < page_size <= size or size % page_size:
            raise ValueError('image dimensions')
        self.size, self.page_size = size, page_size
        self.data = b''
        self.generation = 0
        self.hashes = {}

    @property
    def root(self):
        root = 0
        for value in self.hashes.values():
            root ^= value
        return root

    def apply(self, wire):
        if len(wire) < HEADER.size:
            raise ValueError('header length')
        magic, size, page_size, count, base, generation, old_hash, new_hash, full, *reserved = HEADER.unpack_from(wire)
        if (magic != 0x314d4950 or size != self.size or page_size != self.page_size
                or any(reserved) or full not in (0, 1) or count > size // page_size
                or len(wire) != HEADER.size + count * (4 + page_size)):
            raise ValueError('packet dimensions')
        if (base != self.generation or base == MASK or generation != base + 1
                or old_hash != self.root or bool(full) != (base == 0)
                or (full and count != size // page_size)):
            raise ValueError('generation or baseline')
        # Use a new image and hash map; rejection never changes the consumer.
        image = bytearray(self.data if base else bytes(size))
        hashes = dict(self.hashes)
        indices = []
        for i in range(count):
            offset = HEADER.size + i * (page_size + 4)
            index, = struct.unpack_from('<I', wire, offset)
            if index >= size // page_size or (indices and index <= indices[-1]):
                raise ValueError('page order')
            data = wire[offset + 4:offset + 4 + page_size]
            indices.append(index)
            image[index * page_size:(index + 1) * page_size] = data
            hashes[index] = page_hash(index, data)
        root = 0
        for value in hashes.values():
            root ^= value
        if root != new_hash:
            raise ValueError('page integrity')
        self.data, self.hashes, self.generation = bytes(image), hashes, generation
        return indices


def packet(before, after, page_size, generation):
    """Build an independent reference packet from complete images."""
    if not after or len(after) % page_size or (before and len(before) != len(after)):
        raise ValueError('source dimensions')
    if not 0 <= generation < MASK or bool(before) != bool(generation):
        raise ValueError('source generation')
    records, old_root, new_root = [], 0, 0
    for offset in range(0, len(after), page_size):
        index = offset // page_size
        old, new = before[offset:offset + page_size], after[offset:offset + page_size]
        if before:
            old_root ^= page_hash(index, old)
        new_root ^= page_hash(index, new)
        if not before or old != new:
            records.append(struct.pack('<I', index) + new)
    return HEADER.pack(0x314d4950, len(after), page_size, len(records), generation,
                       generation + 1, old_root, new_root, int(not before), 0, 0, 0) + b''.join(records)
