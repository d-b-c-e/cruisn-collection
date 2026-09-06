"""Strict parsing and effective-RAM verification for explicit patch experiments."""
from pathlib import Path
import struct


def read_patch(path):
    entries = {}
    for line_number, raw in enumerate(Path(path).read_text(encoding="utf-8-sig").splitlines(), 1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        fields = line.split()
        if len(fields) != 3:
            raise ValueError(f"patch line {line_number}: expected address/old/new")
        addr, old, new = fields
        addr, new = int(addr, 16), int(new, 16)
        old = None if old == "*" else int(old, 16)
        if not 0 <= addr < 0x20000 or not 0 <= new <= 0xffffffff or (old is not None and not 0 <= old <= 0xffffffff):
            raise ValueError(f"patch line {line_number}: word/address out of range")
        if addr in entries:
            raise ValueError(f"patch line {line_number}: duplicate word address")
        entries[addr] = (old, new)
    if not entries:
        raise ValueError("empty game patch")
    return entries


def verify_patch_ram(path, entries):
    data = Path(path).read_bytes()
    if len(data) != 0x20000 * 4:
        raise ValueError("program RAM dump must contain exactly 0x20000 words")
    mismatches = []
    for addr, (_, expected) in entries.items():
        actual, = struct.unpack_from("<I", data, addr * 4)
        if actual != expected:
            mismatches.append({"word": addr, "expected": expected, "actual": actual})
    return {"passed": not mismatches, "checked_words": len(entries), "mismatches": mismatches}


def late_patch_lua(entries, frame):
    if any(old is None for old, _ in entries.values()):
        raise ValueError("late patches require an expected old value for every word")
    words = ",\n".join(f"{{{addr},{old},{new}}}" for addr, (old, new) in entries.items())
    return f'''local space = manager.machine.devices[":maincpu"].spaces["program"]
local words = {{{words}}}
return function(frame)
    if frame ~= {frame} then return end
    for _, w in ipairs(words) do
        assert(space:read_u32(w[1]) == w[2], "late game patch guard failed")
    end
    for _, w in ipairs(words) do space:write_u32(w[1], w[3]) end
    emu.print_info("session.lua: game patch {len(entries)} words at frame {frame}")
end
'''
