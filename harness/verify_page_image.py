"""Compare native queued page images against independent complete snapshots.

Use --snapshot for LOCAL WaveRAM files; the default creates synthetic images.
No raw image or packet contents belong in public proof. The report has hashes.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import struct
import subprocess
from page_image import Image, packet
from verification import write_json

SIZE, PAGE = 16777216, 4096


def sha(data):
    return hashlib.sha256(data).hexdigest()


def verify(native, work, snapshots):
    work.mkdir(parents=True, exist_ok=False)
    if not snapshots:
        base = bytes(range(256)) * (SIZE // 256)
        changed = bytearray(base)
        for offset in (0, 4095, 4096, SIZE - 1):
            changed[offset] ^= 91
        changed = bytes(changed)
        distant = bytearray(changed)
        distant[1456*PAGE:1457*PAGE] = b'x' * PAGE
        for i, data in enumerate((base, changed, changed, bytes(distant), base)):
            path = work / f'source-{i}.bin'
            path.write_bytes(data)
            snapshots.append(path)
    if not 1 <= len(snapshots) <= 8:
        raise ValueError('one to eight snapshots required')
    sources = [path.read_bytes() for path in snapshots]
    if any(len(data) != SIZE for data in sources):
        raise ValueError('snapshot size')
    initial = [sha(data) for data in sources]
    native_hash = sha(native.read_bytes())
    env = dict(os.environ)
    if os.name == 'nt':
        env['PATH'] = 'E:/msys64/mingw64/bin;' + env.get('PATH', '')
    result = subprocess.run([str(native), '--stage', str(work / 'native'), *map(str, snapshots)],
                            capture_output=True, text=True, check=True, env=env)
    (work / 'native.stdout').write_text(result.stdout, encoding='utf-8')
    counts = json.loads(result.stdout)['page_counts']
    reference = Image(SIZE, PAGE)
    reports, packets = [], []
    for i, source in enumerate(sources):
        path = work / f'native-{i}.pim'
        wire = path.read_bytes()
        expected = [page for page in range(SIZE // PAGE) if i == 0 or
                    source[page*PAGE:(page+1)*PAGE] != sources[i-1][page*PAGE:(page+1)*PAGE]]
        actual = reference.apply(wire)
        native_image = (work / f'native-{i}.bin').read_bytes()
        if actual != expected or counts[i] != len(expected) or reference.data != source or native_image != source:
            raise ValueError(f'snapshot {i} ownership mismatch')
        reports.append(dict(generation=reference.generation, pages=len(expected),
                            image_sha256=sha(source), packet_sha256=sha(wire),
                            packet_bytes=len(wire), root=reference.root))
        packets.append(path)
    # A Python-generated complete first packet must be byte-identical and must
    # work through the native parser. This exercises the reverse direction.
    generated = work / 'python-first.pim'
    generated.write_bytes(packet(b'', sources[0], PAGE, 0))
    if generated.read_bytes() != packets[0].read_bytes():
        raise ValueError('independent serialization')
    subprocess.run([str(native), '--replay', str(work / 'python-replayed'), str(generated)],
                   capture_output=True, text=True, check=True, env=env)
    if (work / 'python-replayed-0.bin').read_bytes() != sources[0]:
        raise ValueError('independent packet replay')
    # Structural defects must fail before the consumer publishes an image.
    first = bytearray(generated.read_bytes())
    negatives = {'truncated': first[:-1], 'trailing': first + b'\0'}
    for name, offset, value in [('count', 12, 0xffffffff), ('flags', 48, 2), ('reserved', 60, 1)]:
        bad = bytearray(first)
        struct.pack_into('<I', bad, offset, value)
        negatives[name] = bad
    bad = bytearray(first)
    bad[-1] ^= 1
    negatives['last-page-corruption'] = bad
    for name, wire in negatives.items():
        path = work / f'bad-{name}.pim'
        path.write_bytes(wire)
        prefix = work / f'rejected-{name}'
        run = subprocess.run([str(native), '--replay', str(prefix), str(path)],
                             capture_output=True, text=True, env=env)
        if run.returncode == 0 or Path(str(prefix) + '-0.bin').exists():
            raise ValueError(f'accepted malformed packet: {name}')
    if [sha(path.read_bytes()) for path in snapshots] != initial or sha(native.read_bytes()) != native_hash:
        raise ValueError('inputs or native analyzer changed during verification')
    return dict(passed=True, scope='Standalone owned page deltas; no MAME/GPU integration or live residency claim.',
                snapshots=reports, native_sha256=native_hash, reverse_serialization=True,
                malformed_rejections=list(negatives), total_image_bytes=SIZE * len(sources))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--work-dir', type=Path, required=True)
    parser.add_argument('--report', type=Path, required=True)
    parser.add_argument('--snapshot', type=Path, action='append', default=[])
    args = parser.parse_args()
    try:
        report = verify(args.native.resolve(), args.work_dir.resolve(), [p.resolve() for p in args.snapshot])
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        report = dict(passed=False, error=str(error))
    write_json(args.report, report)
    print(json.dumps(report, indent=2))
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
