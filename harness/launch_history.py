"""Keep a bounded history so a successful retry doesn't erase a failed launch."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil


def archive_previous(rig, binary_dir, *, keep=8, limit=2 * 1024 * 1024):
    rig, binary_dir = Path(rig), Path(binary_dir)
    if not (rig / 'launch.log').is_file():
        return
    history = rig / 'launch-history'
    destination = history / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    destination.mkdir(parents=True)
    metadata = {}
    for path in (rig/'launch.log', rig/'launch.json', binary_dir/'midv_gl.log',
                 binary_dir/'midz_gl.log'):
        if not path.is_file():
            continue
        stat = path.stat()
        with path.open('rb') as stream:
            stream.seek(max(0, stat.st_size - limit))
            (destination/path.name).write_bytes(stream.read(limit))
        metadata[path.name] = {'bytes': stat.st_size, 'tail_only': stat.st_size > limit,
                               'modified_utc': datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat()}
    (destination/'archive.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
    # Delete only timestamp directories created by this module, inside this rig.
    owned = sorted(p for p in history.iterdir() if p.is_dir() and
                   len(p.name) == 22 and p.name.endswith('Z') and
                   p.name[:8].isdigit() and p.name[8] == 'T' and p.name[9:21].isdigit())
    for old in owned[:-keep]:
        if old.resolve().parent == history.resolve() and not old.is_symlink():
            shutil.rmtree(old)


def write_receipt(rig, command, environment):
    receipt = {'started_utc': datetime.now(timezone.utc).isoformat(), 'command': command,
               'environment': {k: v for k, v in environment.items() if k.startswith(('MIDV_', 'MIDZ_'))}}
    (Path(rig)/'launch.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
