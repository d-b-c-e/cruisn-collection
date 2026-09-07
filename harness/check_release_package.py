"""Read-only ZIP content checks. This does not certify a clean-machine launch."""
import argparse
import hashlib
from pathlib import Path, PurePosixPath
import zipfile
from verification import sha256_file, write_json

REQUIRED = ('CruisnCollection.exe','CruisnSetup.exe','vunit.exe','SDL2.dll','SDL2-LICENSE.txt',
            'version.txt','setup.ps1','README.txt','force-profiles.ini','lib/toolkit/VERSION',
            'patch/vunit-poc-patches.patch','source/harness/collection.py','source/harness/run_rig.py',
            'source/lua/session.lua','source/gpu/renderer.py')
FREEPLAY = {'crusnusa':('nvram',(0x190,0x195,0x19a,0x19f)), 'crusnwld24':('nvram',(0x1ac,)),
            'crusnwld':('nvram',(0x1ac,)), 'offroadc':('nvram',(0x1cc,)), 'crusnexo':('m48t35',(0x73,))}


def inspect(package, candidate):
    with zipfile.ZipFile(package) as archive:
        entries={}; roots=set()
        for info in archive.infolist():
            name=info.filename.replace('\\','/')
            parts=PurePosixPath(name).parts
            if not parts or name.startswith('/') or ':' in name or '..' in parts:
                raise ValueError('unsafe package path')
            roots.add(parts[0])
            if info.is_dir(): continue
            key='/'.join(parts[1:])
            if not key or key.lower() in entries: raise ValueError('duplicate or unrooted package file')
            entries[key.lower()]=info
        if len(roots)!=1: raise ValueError('expected one package root')
        for name in REQUIRED:
            if name.lower() not in entries or entries[name.lower()].file_size==0:
                raise ValueError(f'missing package dependency: {name}')
        for name in entries:
            if name.startswith(('roms/','rig/')) or name=='dinput8.dll':
                raise ValueError(f'ROM, personal rig data or obsolete plugin in package: {name}')
        binary_hash=hashlib.sha256(archive.read(entries['vunit.exe'])).hexdigest()
        if binary_hash!=sha256_file(candidate): raise ValueError('packaged emulator differs from candidate')
        for rom,(filename,addresses) in FREEPLAY.items():
            data=archive.read(entries[f'fixtures/nvram-{rom}/{filename}'])
            if any(a>=len(data) or data[a]!=1 for a in addresses):
                raise ValueError(f'{rom}: free-play seed is not enabled')
        return {'passed':True,'scope':__doc__,'package_sha256':sha256_file(package),
                'candidate_sha256':binary_hash,'files':len(entries),'root':next(iter(roots))}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('package',type=Path); ap.add_argument('--candidate',required=True,type=Path)
    ap.add_argument('--report',required=True,type=Path)
    args=ap.parse_args()
    try: report=inspect(args.package,args.candidate)
    except (OSError,ValueError,KeyError,zipfile.BadZipFile) as error: report={'passed':False,'error':str(error)}
    write_json(args.report,report)
    print(('PASS' if report['passed'] else 'FAIL')+f': {args.report}')
    return 0 if report['passed'] else 1


if __name__=='__main__': raise SystemExit(main())
