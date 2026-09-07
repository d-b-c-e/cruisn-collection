"""Exercise an extracted Windows release with development paths and physical FFB disabled.

Checks frozen menu pages, setup health, support diagnostics and four neutral
attract boots using completed GL frames and clean WM_CLOSE. This uses the current
Windows installation/drivers; it is not clean-profile or attended drive acceptance.
ROM copies are local to the new evidence directory and never added to the ZIP.
"""
import argparse
import ctypes
import ctypes.wintypes as wt
import json
import os
from pathlib import Path
import shutil
import subprocess
import time
import zipfile

from check_release_package import inspect
from diagnostic_runtime import new_run
from gl_frames import read_completed_frames, requested_frames
from run_regressions import visual_content
from verification import sha256_file, write_json


def game_windows(executable):
    """Return only MAME windows owned by this extracted executable."""
    u=ctypes.windll.user32; k=ctypes.windll.kernel32
    u.GetWindowThreadProcessId.argtypes=[wt.HWND,ctypes.POINTER(wt.DWORD)]
    u.GetClassNameW.argtypes=[wt.HWND,wt.LPWSTR,ctypes.c_int]
    k.OpenProcess.argtypes=[wt.DWORD,wt.BOOL,wt.DWORD];k.OpenProcess.restype=wt.HANDLE
    k.QueryFullProcessImageNameW.argtypes=[wt.HANDLE,wt.DWORD,wt.LPWSTR,ctypes.POINTER(wt.DWORD)]
    k.CloseHandle.argtypes=[wt.HANDLE]
    found=[]
    @ctypes.WINFUNCTYPE(wt.BOOL,wt.HWND,wt.LPARAM)
    def cb(hwnd,_):
        name=ctypes.create_unicode_buffer(64);u.GetClassNameW(hwnd,name,64)
        if name.value!='MAME':return True
        pid=wt.DWORD();u.GetWindowThreadProcessId(hwnd,ctypes.byref(pid))
        handle=k.OpenProcess(0x1000,False,pid.value)
        if handle:
            path=ctypes.create_unicode_buffer(32768);size=wt.DWORD(32768)
            ok=k.QueryFullProcessImageNameW(handle,0,path,ctypes.byref(size));k.CloseHandle(handle)
            if ok and Path(path.value)==executable:found.append(int(hwnd))
        return True
    u.EnumWindows(cb,0)
    return found


def close_game(executable):
    post=ctypes.windll.user32.PostMessageW
    post.argtypes=[wt.HWND,wt.UINT,wt.WPARAM,wt.LPARAM]
    for hwnd in game_windows(executable):post(hwnd,0x10,0,0)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('package',type=Path)
    ap.add_argument('--candidate',required=True,type=Path)
    ap.add_argument('--rom-source',required=True,type=Path)
    ap.add_argument('--output',required=True)
    args=ap.parse_args()
    out=new_run('frozen-package',args.output)
    report={'passed':False,'physical_force':False,'scope':__doc__,
            'package':inspect(args.package,args.candidate),'pages':[],'games':[],'rom_hashes':{}}
    # Exercise spaces and an apostrophe too; the actual frozen entry point must
    # resolve all runtime files beside itself without CRUISN_HOME/ROM overrides.
    install=out/"Player's clean install"
    with zipfile.ZipFile(args.package) as archive:archive.extractall(install)
    app=install/report['package']['root']
    for stem in ('crusnusa','crusnwld','crusnwld24','offroadc','crusnexo',
                 'tms320c31','tms320c32','tms32031','tms32032'):
        for ext in ('.zip','.7z'):
            path=args.rom_source/(stem+ext)
            if path.is_file():
                (app/'roms').mkdir(exist_ok=True)
                shutil.copy2(path,app/'roms'/path.name)
                report['rom_hashes'][path.name]=sha256_file(path)
    env={key:value for key,value in os.environ.items()
         if not key.upper().startswith(('CRUISN_','MIDV_','MIDZ_','SNAP_'))}
    env['PATH']=os.environ['SystemRoot']+'\\System32;'+os.environ['SystemRoot']
    env['MIDV_FFB']='0'
    def save():write_json(out/'report.json',report)
    def run(command):
        result=subprocess.run([str(x) for x in command],cwd=app,env=env,timeout=120,capture_output=True)
        if result.returncode:raise ValueError(f'frozen command failed ({result.returncode}): {command}')
    save()
    try:
        for page in (None,'root','display','ffb','controls','support','graphics','impacts'):
            target=out/f'{page or "menu"}.png'
            command=[app/'CruisnCollection.exe','--shot',target]
            if page:command+=['--shot-page',page]
            run(command)
            report['pages'].append({'page':page,'image_sha256':sha256_file(target)})
        run([app/'CruisnSetup.exe','--health-report',out/'setup-health.json'])
        report['setup_health']=json.loads((out/'setup-health.json').read_text(encoding='utf-8'))
        if not report['setup_health']['passed']:raise ValueError('setup reports incomplete runtime or ROMs')
        save()
        for game in ('usa','world','offroad','exotica'):
            work=out/game;work.mkdir();snap=work/'gl-snap';snap.mkdir()
            key='MIDZ' if game=='exotica' else 'MIDV'
            launch_env=dict(env,**{key+'_GL_SNAP':str(snap),key+'_GL_SNAP_FIRST':'1700',
                key+'_GL_SNAP_LAST':'1800',key+'_GL_SNAP_EVERY':'50',key+'_GL_SNAP_MAX':'3',key+'_GL_LOG':'1'})
            command=[str(app/'CruisnCollection.exe'),'--game',game]
            write_json(work/'invocation.json',{'command':command,'cwd':str(app),
                'physical_force':False,'PATH':env['PATH'],'overrides':{k:v for k,v in launch_env.items() if k.startswith(('MIDV_','MIDZ_'))}})
            proc=subprocess.Popen(command,cwd=app,env=launch_env)
            start=time.monotonic()
            try:
                while proc.poll() is None and time.monotonic()-start<120:
                    if len(list(snap.glob('*.bmp')))>=3:break
                    time.sleep(.5)
            finally:close_game(app/'vunit.exe')
            code=proc.wait(timeout=30)
            row={'game':game,'exit':code,'seconds':time.monotonic()-start,'passed':False}
            for name,path in (('launch.log',app/'rig/launch.log'),('gl.log',app/('midz_gl.log' if game=='exotica' else 'midv_gl.log'))):
                if path.exists():shutil.copy2(path,work/name)
            try:
                row['captures']=len(read_completed_frames(snap,requested_frames(1700,1800,50)))
                row['content']=visual_content(snap)
                log=(work/'launch.log').read_text(errors='replace')
                row['passed']=code==0 and 'MIDV_FFB=0' in log and 'render stream failed' not in log
            except (OSError,ValueError,KeyError) as error:row['error']=str(error)
            report['games'].append(row);save();print(game,'PASS' if row['passed'] else 'FAIL',flush=True)
        run([app/'CruisnSetup.exe','--support-out',out])
        bundles=list(out.glob('CruisnSupport-*.zip'))
        if len(bundles)!=1:raise ValueError('expected one frozen support bundle')
        with zipfile.ZipFile(bundles[0]) as archive:
            joysticks=json.loads(archive.read('joysticks_glfw.json'))
            dump=archive.read('mame_input_dump.txt').decode('utf-8')
            if not isinstance(joysticks,list) or '== port field bindings ==' not in dump:
                raise ValueError('frozen support diagnostics incomplete')
        report['support']={'passed':True,'sha256':sha256_file(bundles[0]),'joysticks':len(joysticks)}
        report['passed']=all(row['passed'] for row in report['games'])
    except (OSError,ValueError,KeyError,subprocess.SubprocessError) as error:
        report['error']=str(error)
    save()
    print('Frozen package','PASS' if report['passed'] else 'FAIL',out/'report.json')
    return 0 if report['passed'] else 1


if __name__=='__main__':raise SystemExit(main())
