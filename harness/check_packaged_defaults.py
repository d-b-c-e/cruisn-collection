"""Check settings inside an extracted frozen release, without starting a game."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from verification import sha256_file, write_json


def check(folder):
    folder=Path(folder).resolve()
    if (folder/'rig').exists():
        raise ValueError('requires a fresh extracted package without a rig directory')
    exe=folder/'CruisnCollection.exe'
    with tempfile.TemporaryDirectory(prefix='cruisn-defaults-') as td:
        output=Path(td)/'defaults.json'
        result=subprocess.run([str(exe),'--config-report',str(output)],cwd=folder,
                              timeout=60,capture_output=True)
        if result.returncode: raise ValueError(f'frozen settings check exited {result.returncode}')
        report=json.loads(output.read_text(encoding='utf-8'))
    state=report['settings']
    if report['saved_config_present'] or (folder/'rig').exists():
        raise ValueError('fresh-default check read or created personal settings')
    if state['crt'] is not True or state['margin'] is not None or state['scale']!=4:
        raise ValueError('release must default to CRT on, full widescreen and scale 4')
    if any(value for game in state['graphics'].values() for key,value in game.items()
           if key!='world_lookahead'):
        raise ValueError('per-game graphics experiments must default off')
    return {'passed':True,'scope':__doc__,'physical_force':False,
            'launcher_sha256':sha256_file(exe),'configuration':report}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('folder',type=Path);ap.add_argument('--report',required=True,type=Path)
    args=ap.parse_args()
    try: report=check(args.folder)
    except (OSError,ValueError,KeyError,subprocess.TimeoutExpired) as error:
        report={'passed':False,'error':str(error)}
    write_json(args.report,report)
    print(('PASS' if report['passed'] else 'FAIL')+f': {args.report}')
    return 0 if report['passed'] else 1


if __name__=='__main__': raise SystemExit(main())
