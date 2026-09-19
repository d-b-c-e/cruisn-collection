"""Attach opt-in UX capabilities to the exact built/reviewed native successor."""
import argparse
import json
from pathlib import Path
from control_launch import FEATURES
from verification import sha256_file

QUALIFIED_SOURCES = {
    '33d44e2c85c4ea5928fb643c51c4aec9ae2d6286': 140,
    '707fd6a8f0a83379e6c96b5b87ee1e24b305bb44': 142,
}


def attach(binary, export):
    binary, export = Path(binary), Path(export)
    receipt = json.loads(export.read_text(encoding='utf-8'))
    digest = sha256_file(binary)
    source = receipt.get('native_commit')
    if (receipt.get('passed') is not True or source not in QUALIFIED_SOURCES
            or receipt.get('candidate_sha256') != digest or receipt.get('patch_count') != QUALIFIED_SOURCES[source]):
        raise ValueError('Exact reviewed native source and successful frozen export required.')
    patch = Path(receipt['patch'])
    if sha256_file(patch) != receipt['patch_sha256']:
        raise ValueError('Native patch series differs from export receipt.')
    features = set(FEATURES)
    if QUALIFIED_SOURCES[source] >= 141:
        features.add('ffb-disconnect-latch-v1')
    value = dict(version=1, sha256=digest, features=sorted(features),
                 native_commit=source, export_sha256=sha256_file(export),
                 scope='software input/output identity and calibration contracts; physical acceptance pending')
    path = Path(str(binary)+'.features.json')
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
    return path


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('binary', type=Path)
    parser.add_argument('export', type=Path)
    args = parser.parse_args()
    print(attach(args.binary, args.export))
