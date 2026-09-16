"""Undamaged static Off-Road billboard descriptor fields, not render admission."""
from offroad_billboard import words
from offroad_sections import span


def descriptor(definition, number, ordinal, count, binding, hit_index, hit_bits):
    words(definition, 11); words(binding, 3); words([hit_index, hit_bits], 2)
    if (any(type(x) is not int for x in (number, ordinal, count)) or
            not 1 <= count <= 256 or not 0 <= ordinal < count or not 0 <= number <= 255):
        raise ValueError('billboard source cardinality')
    flags = definition[0]
    if flags not in (0x804, 0x800804):
        return None
    if flags & 0x800000:
        if hit_index != definition[3] >> 16:
            raise ValueError('billboard damage-state index mismatch')
        if hit_bits & (1 << (hit_index & 31)):
            return None
    if not span(definition[1], 7) or not span(binding[0], 1) or binding[1] > 0x7fff or binding[2] > 0xffff:
        raise ValueError('billboard source model/material span')
    result = [0]*22
    result[5:9] = [flags, ((count-1-ordinal) << 24) | (number << 16) | 0x8000,
                   definition[3], definition[2]]
    result[11:17] = definition[5:11]
    result[17:21] = [*binding, definition[1]]
    return result
