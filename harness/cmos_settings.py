"""Preserve verified game-specific integrity fields when editing operator settings."""


def offroad_checksum(data):
    """Off Road 1.63: ECD5 sums 47 packed words; DB9B..DBA0 checks word 0x35.

    ED96/EDAA encode a big-endian value in the low byte of four consecutive
    32-bit CMOS words. File offsets therefore advance by four bytes per digit.
    Word 0x37 is the settings-layout marker checked at DB93..DB96.
    """
    if len(data) != 0x8000 or bytes(data[0x370:0x380:4]) != b'\0\0\0\x12':
        raise ValueError('unsupported Off Road operator-settings layout')
    expected = sum(int.from_bytes(bytes(data[i:i+16:4]), 'big')
                   for i in range(0, 0x2f0, 16)) & 0xffffffff
    stored = int.from_bytes(bytes(data[0x350:0x360:4]), 'big')
    return expected, stored


def set_bytes(data, rom, filename, addresses, value):
    """Return edited bytes; reject invalid offsets before changing the caller's data."""
    result = bytearray(data)
    addresses = tuple(addresses)
    if any(a < 0 or a >= len(result) for a in addresses):
        raise ValueError('operator setting outside NVRAM')
    for address in addresses:
        result[address] = value & 0xff
    if rom == 'offroadc' and filename == 'nvram' and any(a < 0x2f0 and a % 4 == 0 for a in addresses):
        expected, _ = offroad_checksum(result)
        result[0x350:0x360:4] = expected.to_bytes(4, 'big')
    return result
