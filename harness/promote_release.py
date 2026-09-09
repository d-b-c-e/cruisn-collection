"""Verify a tested ZIP for release; dry-run unless --publish is explicit.

Rechecks all local release gates and the attended ledger against the exact ZIP.
Publication uploads these bytes and tags their recorded commit; it never builds.
"""
import argparse
import json
from pathlib import Path
import re
import subprocess
import tempfile

from check_release_package import inspect, ROOT
from release_identity import source_identity
import release_gate


def verify_identity(manifest, package_report, ledger, current_source):
    if manifest.get('schema') != 1 or manifest.get('source_clean') is not True:
        raise ValueError('candidate must have been assembled from a clean committed checkout')
    if manifest.get('source_identity') != current_source:
        raise ValueError('candidate source is stale')
    for key in ('package_sha256','candidate_sha256','file_hashes','media','version'):
        if manifest.get(key) != package_report.get(key):
            raise ValueError(f'candidate manifest mismatch: {key}')
    version=manifest['version']
    if not re.fullmatch(r'v\d+\.\d+\.\d+(?:-[A-Za-z0-9.-]+)?',version):
        raise ValueError('a release version, not dev, is required')
    if not re.fullmatch(r'[0-9a-f]{40}',manifest.get('commit','')):
        raise ValueError('candidate commit is invalid')
    evidence=ledger.get('checks',{}).get('shared/package-review',{}).get('evidence',[])
    if not any(item.get('sha256')==manifest['package_sha256'] for item in evidence):
        raise ValueError('package-review acceptance must attach the exact ZIP hash')
    return version


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('package',type=Path)
    for name in ('manifest','candidate','checks','regressions','fresh-boots','attended','notes'):
        ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--publish',action='store_true',help='explicitly create the public release after all checks pass')
    args=ap.parse_args()
    manifest=json.loads(args.manifest.read_text(encoding='utf-8'))
    ledger=json.loads(args.attended.read_text(encoding='utf-8'))
    checked=inspect(args.package,args.candidate,media=manifest.get('media',True))
    version=verify_identity(manifest,checked,ledger,source_identity(ROOT)['sha256'])
    subprocess.run(['git','cat-file','-e',manifest['commit']+'^{commit}'],cwd=ROOT,check=True)
    if not args.notes.read_text(encoding='utf-8').strip():
        raise ValueError('reviewed release notes are required')
    with tempfile.TemporaryDirectory(prefix='cruisn-promotion-') as tmp:
        code=release_gate.main(['--candidate',str(args.candidate),'--checks',str(args.checks),'--regressions',str(args.regressions),
            '--fresh-boots',str(args.fresh_boots),'--attended',str(args.attended),
            '--report',str(Path(tmp)/'readiness.json')])
        if code: raise ValueError('release gate is not ready; no publication performed')
    command=['gh','release','create',version,str(args.package.resolve()),
             '--repo','d-b-c-e/cruisn-collection','--target',manifest['commit'],
             '--title',f"Cruis'n Collection {version}",'--notes-file',str(args.notes.resolve())]
    if '-' in version: command+=['--prerelease']
    print(json.dumps({'action':'publish' if args.publish else 'dry-run','command':command,
                      'package_sha256':checked['package_sha256']},indent=2))
    if args.publish:
        tags=subprocess.check_output(['git','ls-remote','--tags','origin',f'refs/tags/{version}',
                                      f'refs/tags/{version}^{{}}'],cwd=ROOT,text=True)
        if tags.strip():raise ValueError('release tag already exists; refusing to replace or retarget it')
        subprocess.run(command,cwd=ROOT,check=True)
    return 0


if __name__=='__main__':
    try: raise SystemExit(main())
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as error:
        raise SystemExit(f'Promotion blocked: {error}')
