"""One-time freeze of the isolated UX lineage; never replaces a personal binary.

Reconstruct every exported patch from mame0286 through a temporary Git index.
The renderer parity patch series is not modified. A successor needs a new output
patch and receipt, rather than overwriting accepted evidence.
"""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from binary_provenance import attach
from verification import sha256_file

BASE = '4ac6a84b51b4ae549399c81ffe1b9346e2c04758'
PERSONAL = '87d04de42d10a731f1d951a1fa378d784059d862063b224764ca6294fa5fe9d8'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native', type=Path, required=True)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--build-log', type=Path, required=True)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--patch', type=Path, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    native = args.native.resolve()
    def git(*words, **kw):
        return subprocess.check_output(['git', '-C', str(native), '-c', 'core.safecrlf=false', *words], **kw)
    if any(p.exists() for p in (args.candidate, args.patch, args.receipt)):
        raise ValueError('retain prior candidate/patch/receipt; use new paths')
    if git('status', '--porcelain').strip():
        raise ValueError('native source must be clean')
    commit = git('rev-parse', 'HEAD').decode().strip()
    if commit != args.commit:
        raise ValueError('unexpected source commit')
    subprocess.run(['git', '-C', str(native), 'merge-base', '--is-ancestor', BASE, commit], check=True)
    binary = native/'build/mingw-gcc/bin/x64/Release/vunit.exe'
    if binary.stat().st_mtime < int(git('show', '-s', '--format=%ct', commit)):
        raise ValueError('binary predates source commit')
    if not args.build_log.is_file() or args.build_log.stat().st_size == 0:
        raise ValueError('retained build log required')
    # The invoking build must have completed successfully; age alone is not proof.
    status = json.loads(args.build_log.with_suffix('.status.json').read_text(encoding='utf-8'))
    if status.get('returncode') != 0 or status.get('native_commit') != commit:
        raise ValueError('successful matching build completion required')
    personal = Path('E:/Source/mame-src/vunit.exe')
    if sha256_file(personal) != PERSONAL:
        raise ValueError('personal binary changed; investigate rather than replace it')
    parity = root/'patch/vunit-poc-patches.patch'
    parity_sha = sha256_file(parity)
    patch = git('format-patch', '--stdout', 'mame0286..'+commit)
    messages = [m for m in re.split(rb'(?m)(?=^From [0-9a-f]{40} Mon Sep 17 00:00:00 2001\r?$)', patch) if m]
    count = int(git('rev-list', '--count', 'mame0286..'+commit))
    if len(messages) != count or count < 135:
        raise ValueError('complete patch series including DIJOYSTATE2 required')
    tree = git('rev-parse', commit+'^{tree}').decode().strip()
    with tempfile.TemporaryDirectory(prefix='ux-native-index-') as temp:
        env = dict(os.environ, GIT_INDEX_FILE=str(Path(temp)/'index'))
        git('read-tree', 'mame0286', env=env)
        for message in messages:
            subprocess.run(['git', '-C', str(native), '-c', 'core.safecrlf=false',
                            'apply', '--cached', '--whitespace=nowarn', '-'], input=message, env=env, check=True)
        if git('write-tree', env=env).decode().strip() != tree:
            raise ValueError('exported series did not reconstruct exact source tree')
    args.candidate.mkdir(parents=True, exist_ok=False)
    shutil.copy2(binary, args.candidate/'vunit.exe')
    shutil.copy2(root/'lib/toolkit/profiles/force-profiles.ini', args.candidate/'force-profiles.ini')
    args.patch.parent.mkdir(parents=True, exist_ok=True)
    with args.patch.open('xb') as stream:
        stream.write(patch)
    if sha256_file(parity) != parity_sha or sha256_file(personal) != PERSONAL:
        raise ValueError('protected parity series/personal binary changed')
    receipt = dict(passed=True, native_commit=commit, tree=tree, accepted_base=BASE,
                   patch_count=count, patch_sha256=sha256_file(args.patch), patch=str(args.patch.resolve()),
                   candidate=str((args.candidate/'vunit.exe').resolve()),
                   candidate_sha256=sha256_file(args.candidate/'vunit.exe'),
                   profile_sha256=sha256_file(args.candidate/'force-profiles.ini'),
                   personal_sha256=PERSONAL, build_log_sha256=sha256_file(args.build_log),
                   parity_patch_unchanged_sha256=parity_sha)
    with args.receipt.open('x', encoding='utf-8') as stream:
        json.dump(receipt, stream, indent=2)
        stream.write('\n')
    attach(args.candidate/'vunit.exe', args.receipt)
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
