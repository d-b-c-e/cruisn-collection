"""Bind a local build attestation to executable bytes; location is not source."""
import argparse
import json
from pathlib import Path
import re
from verification import sha256_file,write_json

FIELDS={'schema','executable_sha256','native_commit','native_tree','patch_sha256','build_log_sha256'}

def receipt_path(executable):return Path(str(executable)+'.build.json')

def validate(data,digest):
    if not isinstance(data,dict) or set(data)!=FIELDS or data['schema']!=1 or type(data['schema']) is not int:
        raise ValueError('invalid executable build receipt schema')
    for key in FIELDS-{'schema'}:
        length=40 if key in ('native_commit','native_tree') else 64
        if not isinstance(data[key],str) or not re.fullmatch('[0-9a-f]{'+str(length)+'}',data[key]):
            raise ValueError('invalid executable build receipt '+key)
    if data['executable_sha256']!=digest:raise ValueError('build receipt does not match executable bytes')
    return data

def read(executable,digest=None):
    path=receipt_path(executable)
    if not path.exists():return None
    if not path.is_file() or path.stat().st_size>16384:raise ValueError('build receipt extent')
    data=validate(json.loads(path.read_text(encoding='utf-8')),digest or sha256_file(executable))
    return dict(kind='binary-build-attestation',commit=data['native_commit'],tree=data['native_tree'],
        executable_sha256=data['executable_sha256'],patch_sha256=data['patch_sha256'],
        build_log_sha256=data['build_log_sha256'],receipt_sha256=sha256_file(path))

def attach(executable,export_receipt):
    path=receipt_path(executable)
    if path.exists():raise ValueError('retain the existing executable build receipt')
    export=Path(export_receipt)
    if not export.is_file() or export.stat().st_size>16384:raise ValueError('native export receipt extent')
    source=json.loads(export.read_text(encoding='utf-8'))
    if not isinstance(source,dict) or source.get('passed') is not True:raise ValueError('native export did not pass')
    data=dict(schema=1,executable_sha256=source['candidate_sha256'],native_commit=source['native_commit'],
        native_tree=source['tree'],patch_sha256=source['patch_sha256'],build_log_sha256=source['build_log_sha256'])
    validate(data,sha256_file(executable));write_json(path,data);return path

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('executable',type=Path)
    ap.add_argument('--export-receipt',type=Path,required=True);args=ap.parse_args()
    print(attach(args.executable,args.export_receipt))
if __name__=='__main__':main()
