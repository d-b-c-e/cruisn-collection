"""Explicit device-free observation of the real native force worker.

No calibration gain is selected here. Host-time conditioning is separate from
emulated-time source writes and from physical wheel acceptance.
"""
import csv
import json
import math
import os
from pathlib import Path
import shutil
import subprocess

from diagnostic_runtime import ROOT
from verification import sha256_file

FILES = ('ffb-worker-receipt.json', 'ffb-worker-ticks.csv', 'ffb-worker-sources.csv')
SOURCE_FIELDS = 'sequence,host_seconds,emulated_seconds,frame,raw,adapted,active,game_invert,device_invert'.split(',')


def add_arguments(parser):
    parser.add_argument('--ffb-worker', choices=('off', 'observe'),
                        help='explicit real force worker with a device-free sink; physical FFB stays off')
    parser.add_argument('--ffb-worker-strength', type=int, help='nominal 0..100; Exotica current 0.8 trim is explicit')
    parser.add_argument('--ffb-worker-impacts', choices=('off', 'on'), help='legacy or enhanced steering impacts')


def configure(args, rom, settings):
    mode = getattr(args, 'ffb_worker', None)
    strength = getattr(args, 'ffb_worker_strength', None)
    impacts = getattr(args, 'ffb_worker_impacts', None)
    if mode is None and settings.get('MIDV_FFB_OBSERVE_WORKER', '0') != '0':
        raise ValueError('worker observation requires an explicit replay option')
    if mode != 'observe':
        if strength is not None or impacts is not None:
            raise ValueError('worker strength/impacts require observation')
        settings['MIDV_FFB_OBSERVE_WORKER'] = '0'
        return None if mode is None else dict(mode='off')
    candidate = getattr(args, 'candidate', None)
    if not candidate or rom not in ('crusnusa', 'crusnwld', 'crusnwld24', 'offroadc', 'crusnexo'):
        raise ValueError('force worker requires an explicit supported-game candidate')
    strength = 50 if strength is None else strength
    if not 0 <= strength <= 100:
        raise ValueError('worker strength must be 0..100')
    effective = (strength * 80 + 50) // 100 if rom == 'crusnexo' else strength
    profiles = Path(candidate).resolve().parent
    if ((profiles/'force-profiles.user.ini').exists() or
            sha256_file(profiles/'force-profiles.ini') != sha256_file(ROOT/'lib/toolkit/profiles/force-profiles.ini')):
        raise ValueError('worker candidate requires the unmodified shipped profiles and no user override')
    # A common named profile, with no inherited developer smoothing override.
    settings.pop('MIDV_FFB_SMOOTH', None)
    settings.pop('MIDV_FFB_TEST', None)
    settings.update(MIDV_FFB='0', MIDV_FFB_OBSERVE_WORKER='1',
                    MIDV_FFB_PROFILE='cruisn-vunit@2', MIDV_FFB_STRENGTH=str(effective),
                    MIDV_FFB_IMPACT='1' if impacts == 'on' else '0')
    wanted = dict(profile='cruisn-vunit@2', smoothing_ms=20, strength=effective, impact_axis=impacts == 'on')
    for key, env, default, maximum in (
            ('hold_ms', 'HOLD_MS', 500, 60000), ('damper', 'DAMPER', 0, 100),
            ('friction', 'FRICTION', 0, 100), ('spring', 'SPRING', 0, 100),
            ('rumble', 'RUMBLE', 0, 100), ('invert', 'INVERT', 0, 1)):
        value = int(settings.get('MIDV_FFB_'+env, str(default)))
        if not 0 <= value <= maximum:
            raise ValueError('invalid recorded worker '+key)
        wanted[key] = bool(value) if key == 'invert' else value
    return dict(mode=mode, nominal_strength=strength, effective_strength=effective,
                profiles=str(profiles), profiles_sha256=sha256_file(profiles/'force-profiles.ini'),
                expected=wanted, physical_output=False, physical_acceptance=False)


def prepare(trial, work):
    if not trial or trial['mode'] == 'off':
        return
    work = Path(work); binary = work/('ffb-worker-verifier.exe' if os.name == 'nt' else 'ffb-worker-verifier')
    compiler = Path(shutil.which('g++') or 'E:/msys64/mingw64/bin/g++.exe').resolve()
    env = dict(os.environ, PATH=str(compiler.parent)+os.pathsep+os.environ.get('PATH', ''))
    command = [str(compiler), '-std=c++11', '-O2', '-Wall', '-Wextra',
               '-I'+str(ROOT/'lib/toolkit/include'), str(ROOT/'native/verify_ffb_worker.cpp'), '-o', str(binary)]
    with (work/'ffb-worker-build.log').open('w') as log:
        subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
    trial.update(verifier=str(binary), verifier_sha256=sha256_file(binary), compiler_directory=str(compiler.parent),
                 source_sha256=sha256_file(ROOT/'native/verify_ffb_worker.cpp'))


def bounded_sources(path):
    if not 0 < path.stat().st_size <= 64*1024*1024:
        raise ValueError('worker source byte bound')
    with path.open(encoding='ascii', newline='') as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != SOURCE_FIELDS:
            raise ValueError('worker source schema')
        rows = []
        for row in reader:
            if None in row or any(v is None for v in row.values()) or len(rows) >= 131072:
                raise ValueError('worker source record bound/shape')
            v = {k: float(row[k]) if k.endswith('seconds') else int(row[k]) for k in SOURCE_FIELDS}
            if (v['sequence'] != len(rows)+1 or
                    not all(math.isfinite(v[k]) and v[k] >= 0 for k in ('host_seconds','emulated_seconds','frame')) or
                    not all(v[k] in (0,1) for k in ('active','game_invert','device_invert')) or
                    not all(-128 <= v[k] <= 127 for k in ('raw','adapted'))):
                raise ValueError('worker source range/order')
            if rows and any(v[k] < rows[-1][k] for k in ('host_seconds','emulated_seconds','frame')):
                raise ValueError('worker source clocks reversed')
            rows.append(v)
    if not rows:
        raise ValueError('empty worker sources')
    return rows


def verify_receipt(trial, directory):
    directory = Path(directory)
    text = (directory/'stdout.log').read_text(encoding='utf-8', errors='replace')
    text += (directory/'stderr.log').read_text(encoding='utf-8', errors='replace')
    acknowledgment = 'MIDV_FFB_WORKER_OBSERVE=1 physical_output=0'
    if not trial or trial['mode'] == 'off':
        if acknowledgment in text or any((directory/name).exists() for name in FILES):
            raise ValueError('disabled force worker observer ran')
        return None
    invocation = json.loads((directory/'invocation.json').read_text(encoding='utf-8'))
    env = invocation['environment']
    if (env.get('MIDV_FFB') != '0' or env.get('MIDV_FFB_OBSERVE_WORKER') != '1' or
            'MIDV_FFB_TEST' in env or text.count(acknowledgment) != 1 or 'FFB worker journal incomplete' in text):
        raise ValueError('worker output-free invocation/acknowledgment')
    profiles = Path(trial['profiles'])
    if ((profiles/'force-profiles.user.ini').exists() or
            sha256_file(profiles/'force-profiles.ini') != trial['profiles_sha256']):
        raise ValueError('worker profile changed during run')
    path = directory/FILES[0]
    if path.stat().st_size > 8192:
        raise ValueError('worker receipt bound')
    receipt = json.loads(path.read_text(encoding='ascii'))
    if (receipt.get('schema') != 1 or receipt.get('complete') is not True or
            receipt.get('device_free') is not True or receipt.get('physical_output') is not False or
            receipt.get('profile_loaded') is not True or receipt.get('sink_final_level') != 0):
        raise ValueError('incomplete force worker receipt')
    if any(receipt.get(k) != v for k, v in trial['expected'].items()):
        raise ValueError('effective worker settings mismatch')
    for kind, name in (('tick', FILES[1]), ('source', FILES[2])):
        size = (directory/name).stat().st_size
        if not 0 < size <= 64*1024*1024 or size != receipt[kind+'_bytes']:
            raise ValueError('worker journal extent')
    rows = bounded_sources(directory/FILES[2])
    if len(rows) != receipt['sources'] or any(bool(r['device_invert']) != receipt['invert'] for r in rows):
        raise ValueError('worker source count/polarity')
    # Independent emulated-source join. Precision of this older CSV is 1 ns.
    if (directory/'force-source.csv').stat().st_size > 64*1024*1024:
        raise ValueError('original source byte bound')
    with (directory/'force-source.csv').open(encoding='ascii', newline='') as f:
        source = list(csv.DictReader(line for line in f if not line.startswith('#')))
    if len(source) != len(rows) or any(
            int(s['frame']) != r['frame'] or int(s['raw']) != r['raw'] or int(s['adapted']) != r['adapted'] or
            abs(float(s['seconds'])-r['emulated_seconds']) > 0.5001e-9 for s,r in zip(source,rows)):
        raise ValueError('worker original source join')
    binary = Path(trial['verifier'])
    if sha256_file(binary) != trial['verifier_sha256']:
        raise ValueError('worker verifier changed')
    args = [str(binary), str(directory/FILES[1]), str(profiles), receipt['profile'],
            str(receipt['strength']), str(receipt['smoothing_ms']), str(receipt['hold_ms']),
            str(int(receipt['impact_axis'])), str(receipt['rumble'])]
    run_env = dict(os.environ, PATH=trial['compiler_directory']+os.pathsep+os.environ.get('PATH',''))
    run = subprocess.run(args, env=run_env, capture_output=True, text=True, timeout=120)
    (directory/'ffb-worker-verifier.log').write_text(run.stdout+run.stderr, encoding='utf-8')
    if run.returncode:
        raise ValueError('worker stage replay failed: '+run.stderr.strip())
    result = json.loads(run.stdout)
    stop = receipt['stop_host_seconds']
    if (result['passed'] is not True or result['ticks'] != receipt['ticks'] or not math.isfinite(stop) or
            stop < max(result['last_host_seconds'], rows[-1]['host_seconds'])):
        raise ValueError('worker finish/count mismatch')
    result.update(receipt=receipt, source_join_rows=len(rows),
                  hashes={name:sha256_file(directory/name) for name in FILES},
                  mailbox_causality_verified=False, physical_acceptance=False,
                  scope='Actual observed conditioning inputs/clocks; sink acceptance is not physical delivery')
    return result
