"""Stage optional exact native provenance/capabilities without personal state."""
import argparse
import json
from pathlib import Path
import shutil

import binary_provenance
from control_launch import supported
from verification import sha256_file


def stage(binary, destination, source_root):
    binary, destination, source_root = map(Path, (binary, destination, source_root))
    receipt = binary_provenance.read(binary)
    features = Path(str(binary)+'.features.json')
    if features.exists() and (receipt is None or not supported(binary)):
        raise ValueError('Control capabilities require matching native provenance and executable bytes.')
    if receipt is None:
        return None  # Historical accepted native without a build receipt.
    patches = [path for path in (source_root/'patch').rglob('*.patch')
               if sha256_file(path) == receipt['patch_sha256']]
    if not patches:
        raise ValueError('No exact corresponding native source patch in the source checkout.')
    if features.exists():
        capability = json.loads(features.read_text(encoding='utf-8'))
        if capability.get('native_commit') != receipt['commit']:
            raise ValueError('Control capability and native build sources differ.')
    if sha256_file(destination/'vunit.exe') != receipt['executable_sha256']:
        raise ValueError('Staged executable differs from native receipt.')
    # The canonical reconstruction instructions must name the series for THIS
    # executable, not whichever experimental native worktree was most recent.
    (destination/'patch').mkdir(exist_ok=True)
    shutil.copyfile(patches[0], destination/'patch/vunit-poc-patches.patch')
    shutil.copyfile(binary_provenance.receipt_path(binary), destination/'vunit.exe.build.json')
    if features.exists():
        shutil.copyfile(features, destination/'vunit.exe.features.json')
    return receipt


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('destination', type=Path)
    parser.add_argument('--source-root', type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    print(json.dumps(stage(args.binary, args.destination, args.source_root), indent=2))
