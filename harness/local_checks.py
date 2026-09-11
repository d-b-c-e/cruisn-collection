"""Run the ROM-free Python, native and GPU checks without GitHub Actions.

Each run owns a new output directory. Report commands, exit codes, source hashes
and evidence hashes; fail on missing tools, failed steps or changing source.
This does not build MAME, launch games, drive a wheel or publish a release.
"""
import argparse
from datetime import datetime, timezone
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
import unittest

from release_identity import source_identity
from verification import sha256_file, write_json

ROOT = Path(__file__).resolve().parents[1]
GROUPS = ('python', 'native', 'gpu')


def unit_worker(path):
    suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = result.wasSuccessful() and result.testsRun > 0
    # Linux intentionally lacks the Windows launcher/device-configuration tests.
    # The release gate requires a Windows report with no skipped tests.
    if sys.platform == 'win32' and result.skipped:
        passed = False
    write_json(path, {'passed': passed, 'tests': result.testsRun,
                     'skipped': len(result.skipped), 'failures': len(result.failures),
                     'errors': len(result.errors)})
    return 0 if passed else 1


def commands(group, output, cxx):
    """The same command inventory is used by local runs and hosted fallbacks."""
    py = sys.executable
    exe_suffix = '.exe' if os.name == 'nt' else ''
    if group == 'python':
        return [('python-tests', [py, str(Path(__file__).resolve()), '--unit-worker',
                                  str(output/'unit-tests.json')])]
    if group == 'gpu':
        return [('gpu-quality', [py, 'harness/verify_quality.py', '--report',
                                 str(output/'gpu-quality.json')]),
                ('zeus-policy-pixels',[py,'harness/verify_zeus_policy.py','--report',str(output/'zeus-policy-pixels.json')]),
                ('zeus-palette-pixels',[py,'harness/verify_zeus_palette.py','--report',str(output/'zeus-palette-pixels.json')]),
                ('zeus-margin-pixels',[py,'harness/verify_zeus_margin_clear.py','--report',str(output/'zeus-margin-pixels.json')]),
                ('zeus-sky-pixels',[py,'harness/verify_zeus_sky_pixels.py','--report',str(output/'zeus-sky-pixels.json')]),
                ('gl-readback',[py,'harness/verify_gl_readback.py','--report',str(output/'gl-readback.json')]),
                ('zeus-private-margin-depth',[py,'harness/verify_zeus_margin_depth.py','--report',str(output/'zeus-private-margin-depth.json')]),
                ('zeus-depth-domain',[py,'harness/verify_zeus_depth_domain.py','--report',str(output/'zeus-depth-domain.json')]),
                ('zeus-depth-mirror',[py,'harness/verify_zeus_depth_mirror.py','--report',str(output/'zeus-depth-mirror.json')]),
                ('zeus-wide-depth',[py,'harness/verify_zeus_wide_depth.py','--report',str(output/'zeus-wide-depth.json')])]
    steps = [('compiler-version', [cxx, '--version'])]

    def compile_one(name, source):
        binary = output/'bin'/(name+exe_suffix)
        steps.append(('compile-'+name, [cxx, '-std=c++11', '-O2', '-Wall', '-Wextra',
                      '-Inative', '-Ilib/toolkit/include', source, '-o', str(binary)]))
        return str(binary)

    # New standalone native tests are automatically included.
    for source in sorted((ROOT/'tests/native').glob('*_test.cpp')):
        binary = compile_one(source.stem, source.relative_to(ROOT).as_posix())
        steps.append(('run-'+source.stem, [binary]))
    host = compile_one('world-host', 'native/analyze_world_host.cpp')
    compile_one('world-future', 'native/analyze_world_future.cpp')
    compile_one('usa-model', 'native/analyze_usa_model.cpp')
    compile_one('offroad-model', 'native/analyze_offroad_model.cpp')
    compile_one('exotica-transform', 'native/analyze_exotica_transform.cpp')
    compile_one('exotica-state', 'native/analyze_exotica_state.cpp')
    fade = compile_one('exotica-fade', 'native/analyze_exotica_fade.cpp')
    steps.append(('exotica-fade-inputs', [py, 'tests/native/check_exotica_fade.py', fade]))
    lifetimes = compile_one('scenery-lifetimes', 'native/analyze_scenery_lifetimes.cpp')
    steps.append(('scenery-lifetime-inputs', [py, 'tests/native/check_scenery_lifetimes.py', lifetimes]))
    compile_one('exotica-future', 'native/analyze_exotica_future.cpp')
    compile_one('exotica-scene', 'native/analyze_exotica_scene.cpp')
    compile_one('exotica-active', 'native/analyze_exotica_active.cpp')
    compile_one('zeus-models', 'native/analyze_zeus_models.cpp')
    compile_one('zeus-state', 'native/analyze_zeus_state.cpp')
    compile_one('zeus-sky', 'native/analyze_zeus_sky.cpp')
    pages = compile_one('page-image', 'native/analyze_page_image.cpp')
    steps.append(('page-image-ownership', [py, 'harness/verify_page_image.py', '--native', pages,
                  '--work-dir', str(output/'page-images'), '--report', str(output/'page-images.json')]))
    bounds = compile_one('zeus-bounds', 'native/analyze_zeus_bounds.cpp')
    steps.append(('zeus-bounds-projection', [py, 'harness/verify_zeus_bounds.py', '--native', bounds,
                  '--work-dir', str(output/'bounds-batch'), '--report', str(output/'zeus-bounds.json')]))
    compile_one('offroad-future', 'native/analyze_offroad_future.cpp')
    compile_one('usa-host', 'native/analyze_usa_host.cpp')
    compile_one('usa-future', 'native/analyze_usa_future.cpp')
    steps.append(('world-host-math', [py, 'harness/verify_world_host_native.py', host,
                                    '--report', str(output/'world-host-math.json')]))
    ffb = compile_one('ffb-analyzer', 'native/analyze_ffb.cpp')
    base = [ffb, 'fixtures/signals/idle-hit.csv', 'lib/toolkit/profiles', 'cruisn-vunit@2', '50']
    steps += [('ffb-stages', base+[str(output/'stages.csv')]),
              ('ffb-impacts', base+[str(output/'impacts.csv'), '--impacts']),
              ('motor-adapter', [py, 'tests/native/check_motor_adapter.py', ffb])]
    junctions = compile_one('tjunctions', 'native/analyze_tjunctions.cpp')
    steps.append(('tjunctions', [py, 'tests/native/check_tjunctions.py', junctions]))
    return steps


def find_compiler(explicit=None):
    selected = explicit or os.environ.get('CXX')
    if selected:
        found = shutil.which(selected)
        if not found:
            raise ValueError(f'C++ compiler not found: {selected}')
        return str(Path(found).resolve())
    found = shutil.which('g++')
    if not found and os.name == 'nt':
        fallback = Path('E:/msys64/mingw64/bin/g++.exe')
        if fallback.is_file():
            found = str(fallback)
    if not found:
        raise ValueError('g++ is required; use --cxx PATH or set CXX to its executable')
    return str(Path(found).resolve())


def run_command(name, command, output, env):
    log = output/(name+'.log')
    started = time.monotonic()
    error = None
    with log.open('wb') as stream:
        try:
            code = subprocess.run(command, cwd=ROOT, env=env, stdout=stream,
                                  stderr=subprocess.STDOUT, timeout=600).returncode
        except (OSError, subprocess.TimeoutExpired) as exc:
            error = str(exc)
            stream.write(error.encode('utf-8', errors='replace'))
            code = -1
    row = {'name': name, 'command': command, 'returncode': code,
           'seconds': round(time.monotonic()-started, 3), 'log': log.name}
    if error:
        row['error'] = error
    print(f"{'PASS' if code == 0 else 'FAIL'} {name} ({row['seconds']:.1f}s)", flush=True)
    return row


def validate_report(report, source_hash, directory):
    """Release acceptance: complete Windows coverage and intact local evidence."""
    try:
        if not (report['schema'] == 1 and report['passed'] is True
                and report['groups'] == list(GROUPS) and report['platform'] == 'win32'
                and report['source_identity'] == report['source_identity_after'] == source_hash):
            return False
        expected = [name for group in GROUPS for name, _ in commands(group, directory, 'g++')]
        if [step['name'] for step in report['steps']] != expected:
            return False
        if any(step['returncode'] != 0 for step in report['steps']):
            return False
        required = {'source-identity.json', 'unit-tests.json', 'gpu-quality.json',
                    'world-host-math.json', 'stages.csv', 'impacts.csv'}
        required.update(step['log'] for step in report['steps'])
        if not required.issubset(report['artifacts']):
            return False
        for name, digest in report['artifacts'].items():
            path = (directory/name).resolve()
            if not path.is_relative_to(directory.resolve()) or sha256_file(path) != digest:
                return False
        units = json.loads((directory/'unit-tests.json').read_text())
        gpu = json.loads((directory/'gpu-quality.json').read_text())
        math = json.loads((directory/'world-host-math.json').read_text())
        identity = json.loads((directory/'source-identity.json').read_text())
        return (units['passed'] is True and units['tests'] > 0 and units['skipped'] == 0
                and units['errors'] == units['failures'] == 0
                and identity['sha256'] == source_hash
                and math['passed'] is True and math['math_passed'] is True and math['math_vectors'] > 0
                and gpu['passed'] is True and bool(gpu['checks'])
                and all(row['passed'] is True for row in gpu['checks']))
    except (OSError, ValueError, KeyError, TypeError):
        return False


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path, help='new directory (default: timestamped results/diagnostics/local-checks-*)')
    ap.add_argument('--group', choices=('all',)+GROUPS, default='all',
                    help='subset runs do not satisfy the release gate')
    ap.add_argument('--cxx', help='g++ executable path, otherwise CXX/PATH/local MSYS2')
    ap.add_argument('--unit-worker', type=Path, help=argparse.SUPPRESS)
    args = ap.parse_args(argv)
    if args.unit_worker:
        return unit_worker(args.unit_worker)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S-%f')
    output = (args.output or ROOT/'results/diagnostics'/('local-checks-'+stamp)).resolve()
    output.mkdir(parents=True, exist_ok=False)
    (output/'bin').mkdir()
    groups = GROUPS if args.group == 'all' else (args.group,)
    identity = source_identity(ROOT)
    write_json(output/'source-identity.json', identity)
    report = {'schema': 1, 'passed': False, 'platform': sys.platform,
              'host': platform.platform(), 'python': sys.version, 'executable': sys.executable,
              'groups': list(groups), 'source_identity': identity['sha256'], 'steps': []}
    report['packages'] = {}
    for package in ('numpy', 'Pillow', 'moderngl', 'lupa'):
        try:
            report['packages'][package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            report['packages'][package] = None
    try:
        cxx = find_compiler(args.cxx) if 'native' in groups else None
        env = dict(os.environ)
        if cxx:
            # MinGW executables and cc1plus need sibling DLLs. Keep the parent
            # Python interpreter explicit so changing PATH cannot switch Python.
            env['PATH'] = str(Path(cxx).parent)+os.pathsep+env.get('PATH', '')
        for group in groups:
            for name, command in commands(group, output, cxx):
                row = run_command(name, command, output, env)
                report['steps'].append(row)
                if row['returncode'] != 0:
                    break  # Never execute a stale binary after compilation fails.
        report['source_identity_after'] = source_identity(ROOT)['sha256']
        expected = [name for group in groups for name, _ in commands(group, output, cxx)]
        report['passed'] = (report['source_identity_after'] == identity['sha256']
                            and [row['name'] for row in report['steps']] == expected
                            and all(row['returncode'] == 0 for row in report['steps']))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        report['error'] = str(exc)
    report['artifacts'] = {path.name: sha256_file(path) for path in sorted(output.iterdir())
                           if path.is_file()}
    write_json(output/'report.json', report)
    print(f"Local checks {'PASS' if report['passed'] else 'FAIL'}: {output/'report.json'}")
    return 0 if report['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
