"""Read-only ZIP content checks. This does not certify a clean-machine launch."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import zipfile
from verification import sha256_file, write_json
from cmos_settings import offroad_checksum
from release_identity import source_identity

ROOT = Path(__file__).resolve().parents[1]

REQUIRED = ('CruisnCollection.exe','CruisnSetup.exe','vunit.exe','SDL2.dll','SDL2-LICENSE.txt',
            'version.txt','setup.ps1','README.txt','force-profiles.ini','lib/toolkit/VERSION',
            'patch/vunit-poc-patches.patch','source/harness/collection.py','source/harness/run_rig.py',
            'source/lua/session.lua','source/lua/cheats.lua','source/harness/cheats.py',
            'source/gpu/renderer.py','source/native/cpu_upload_spans.h',
            'source/lib/toolkit/LICENSE','bgfx/chains/crt-geom-deluxe.json','bgfx/LICENSE',
            'MAME-COPYING.txt','licenses/mame/GPL-2.0')
MEDIA = ('art/Clear Logo/Cruis_n USA-01.png','art/Clear Logo/Cruis_n World-01.png',
         'art/Clear Logo/Off Road Challenge-01.png','art/Clear Logo/North America/Cruis_n Exotica-01.png',
         'art/Screenshot - Game Title/Cruis_n USA-01.jpg','art/Screenshot - Game Title/Cruis_n World-01.png',
         'art/Screenshot - Game Title/Off Road Challenge-01.png','art/Screenshot - Game Title/Cruis_n Exotica-02.png',
         'audio/menumusic.mp3')
FREEPLAY = {'crusnusa':('nvram',(0x190,0x195,0x19a,0x19f)), 'crusnwld24':('nvram',(0x1ac,)),
            'crusnwld':('nvram',(0x1ac,)), 'offroadc':('nvram',(0x1cc,)), 'crusnexo':('m48t35',(0x73,))}


def inspect(package, candidate, *, media=True):
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
        for name in REQUIRED + (MEDIA if media else ()):
            if name.lower() not in entries or entries[name.lower()].file_size==0:
                raise ValueError(f'missing package dependency: {name}')
        for name in entries:
            if name.startswith(('roms/','rig/')) or name=='dinput8.dll':
                raise ValueError(f'ROM, personal rig data or obsolete plugin in package: {name}')
            if not media and name.startswith(('art/','audio/')):
                raise ValueError('media found in requested no-media package')
            if '/__pycache__/' in name or name.endswith('.pyc'):
                raise ValueError(f'loose development bytecode in package: {name}')
        binary_hash=hashlib.sha256(archive.read(entries['vunit.exe'])).hexdigest()
        if binary_hash!=sha256_file(candidate): raise ValueError('packaged emulator differs from candidate')
        for rom,(filename,addresses) in FREEPLAY.items():
            data=archive.read(entries[f'fixtures/nvram-{rom}/{filename}'])
            if any(a>=len(data) or data[a]!=1 for a in addresses):
                raise ValueError(f'{rom}: free-play seed is not enabled')
            if rom == 'offroadc':
                expected, stored = offroad_checksum(data)
                if expected != stored:
                    raise ValueError('offroadc: operator-settings checksum is invalid')
        return {'passed':True,'scope':__doc__,'package_sha256':sha256_file(package),
                'candidate_sha256':binary_hash,'files':len(entries),'root':next(iter(roots)),
                'media':media,'version':archive.read(entries['version.txt']).decode('utf-8-sig').strip(),
                'file_hashes':{name:hashlib.sha256(archive.read(info)).hexdigest() for name,info in entries.items()}}


def candidate_manifest(report, package, root=ROOT):
    identity=source_identity(root)
    dirty=subprocess.check_output(['git','status','--porcelain','--untracked-files=all'],cwd=root).decode()
    return {'schema':1,'package':Path(package).name,'package_sha256':report['package_sha256'],
            'candidate_sha256':report['candidate_sha256'],'version':report['version'],'media':report['media'],
            'commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root).decode().strip(),
            'source_clean':not dirty.strip(),'source_identity':identity['sha256'],
            'file_hashes':report['file_hashes']}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('package',type=Path); ap.add_argument('--candidate',required=True,type=Path)
    ap.add_argument('--report',required=True,type=Path)
    ap.add_argument('--no-media',action='store_true')
    ap.add_argument('--write-manifest',type=Path,help='bind an immutable ZIP to this source and all packaged files')
    args=ap.parse_args()
    try:
        report=inspect(args.package,args.candidate,media=not args.no_media)
        if args.write_manifest:
            with args.write_manifest.open('x',encoding='utf-8') as out:
                json.dump(candidate_manifest(report,args.package),out,indent=2)
    except (OSError,ValueError,KeyError,zipfile.BadZipFile) as error: report={'passed':False,'error':str(error)}
    write_json(args.report,report)
    print(('PASS' if report['passed'] else 'FAIL')+f': {args.report}')
    return 0 if report['passed'] else 1


if __name__=='__main__': raise SystemExit(main())
