"""Compile actual attachment/output functions with fake SDL; no physical output."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
PREFIX = r'''
#define SDL_MAIN_HANDLED
#include <windows.h>
#include <SDL2/SDL.h>
#include <atomic>
#include <cassert>
#include <condition_variable>
#include <cstring>
#include <future>
#include <iostream>
#include <mutex>
#include <string>
#include "ffb_device_selection.h"
static std::atomic<bool> s_user_stopped{false};
static std::atomic<bool> s_user_stop_saved{false},s_user_stop_persist_pending{false},s_running{true};
static std::mutex s_output_mtx;
static double s_worker_user_stop_ack=-1.;
static bool s_observe_worker=false;
static int s_worker_sink_level=0;
static unsigned s_worker_condition_mask=0;
static float s_worker_rumble=0;
static bool attached=true;
static Sint32 instance=123;
static std::string path="\\\\?\\HID#ONE";
static int polls=0,latches=0,positive=0;
static std::atomic<int> stops{0},file_attempts{0};
static int stop_result=0;
static bool block_flush=false,flush_entered=false,release_flush=false,flush_success=true;
static std::mutex persistence_mutex;
static std::condition_variable persistence_cv;
void flog(char const *,...) {}
void osd_printf_info(char const *,...) {}
void worker_output_trace(char const *,int,double) {}
void midv_ffb_cancel() { assert(s_user_stopped);++latches; }
double worker_host_seconds() { return 1.; }
wchar_t const *fake_wgetenv(wchar_t const *) { return L"fixture-no-file-access"; }
HANDLE fake_CreateFileW(LPCWSTR,DWORD,DWORD,LPSECURITY_ATTRIBUTES,DWORD,DWORD,HANDLE) {
    assert(s_user_stopped && stops>=2);++file_attempts;return reinterpret_cast<HANDLE>(1);
}
BOOL fake_FlushFileBuffers(HANDLE) {
    std::unique_lock<std::mutex> lock(persistence_mutex);
    flush_entered=true;persistence_cv.notify_all();
    if(block_flush)persistence_cv.wait(lock,[]{return release_flush;});
    return flush_success;
}
BOOL fake_CloseHandle(HANDLE) { return TRUE; }
#define _wgetenv fake_wgetenv
#define CreateFileW fake_CreateFileW
#define FlushFileBuffers fake_FlushFileBuffers
#define CloseHandle fake_CloseHandle
void p_SDL_JoystickUpdate() { ++polls; }
char const *p_SDL_JoystickPath(SDL_Joystick *) { return path.c_str(); }
SDL_bool p_SDL_JoystickGetAttached(SDL_Joystick *) { return attached?SDL_TRUE:SDL_FALSE; }
Sint32 p_SDL_JoystickInstanceID(SDL_Joystick *) { return instance; }
int p_SDL_HapticUpdateEffect(SDL_Haptic *,int,SDL_HapticEffect *e) { assert(e->constant.level>0);++positive;return 0; }
int p_SDL_HapticRunEffect(SDL_Haptic *,int,Uint32) { ++positive;return 0; }
int p_SDL_HapticStopEffect(SDL_Haptic *,int) { ++stops;return stop_result; }
int p_SDL_HapticRumblePlay(SDL_Haptic *,float,Uint32) { ++positive;return 0; }
int p_SDL_HapticRumbleStop(SDL_Haptic *) { ++stops;return stop_result; }
int p_SDL_HapticStopAll(SDL_Haptic *) { ++stops;return stop_result; }
char const *p_SDL_GetError() { return "fixture"; }
'''
SUFFIX = r'''
int main()
{
    for (int loss=0;loss<4;++loss) {
        Device d;d.instance=123;d.path="\\\\?\\hid#one";d.is_wheel=true;
        s_user_stopped=false;s_observe_worker=false;attached=true;instance=123;path=d.path;
        polls=latches=positive=stops=0;stop_result=0;s_user_stop_persist_pending=false;file_attempts=0;
        assert(check_output_attachment(d,0));assert(polls==1);
        assert(check_output_attachment(d,49));assert(polls==1);
        assert(check_output_attachment(d,50));assert(polls==2);
        bool running=false;int applied=0;
        apply(d,12000,running,applied);condition_output(d,1,true);rumble_output(d,.5f);
        assert(positive==4 && applied==12000);
        if(loss==0)attached=false;
        if(loss==1)instance=-1;
        if(loss==2)instance=456;
        if(loss==3)path="\\\\?\\hid#replacement";
        assert(!check_output_attachment(d,100));assert(latches==1 && s_user_stopped);
        assert(file_attempts==0); // Detection alone may not block on disk.
        int prior=positive;
        apply(d,30000,running,applied);condition_output(d,1,true);rumble_output(d,1.f);stop_all_output(d);
        assert(positive==prior && applied==0 && stops==4);
        // Even if the backend reports attachment again, this worker cannot
        // select/reopen it or deliver new positive effects after loss.
        attached=true;instance=123;path=d.path;
        assert(!check_output_attachment(d,1000));assert(latches==1 && polls==3);
        apply(d,30000,running,applied);condition_output(d,2,true);rumble_output(d,1.f);
        assert(positive==prior);
        stop_result=-1;assert(stop_all_output(d)==-1);assert(rumble_output(d,0.f)==-1);
    }
    // Execute the REAL latch, cancellation service and persistence functions.
    // A deliberately blocked FlushFileBuffers must find all stops attempted.
    for(bool fail_api:{false,true}) {
        Device d;d.instance=123;d.path=path;d.is_wheel=true;
        attached=true;instance=123;s_user_stopped=false;s_user_stop_saved=false;s_user_stop_persist_pending=false;
        stops=0;file_attempts=0;stop_result=fail_api?-1:0;
        bool running=true,ack=false;int applied=12000;
        assert(latch_user_stop());assert(stops==0 && file_attempts==0);
        block_flush=true;flush_entered=release_flush=false;flush_success=!fail_api;
        auto owner=std::async(std::launch::async,[&]{
            std::lock_guard<std::mutex> guard(s_output_mtx);
            service_user_stop(d,running,applied,true,ack);
        });
        {
            std::unique_lock<std::mutex> lock(persistence_mutex);
            assert(persistence_cv.wait_for(lock,std::chrono::seconds(2),[]{return flush_entered;}));
            assert(stops==3 && file_attempts==1 && s_user_stopped && !s_user_stop_saved);
            release_flush=true;persistence_cv.notify_all();
        }
        owner.get();assert(applied==0 && ack==!fail_api && s_user_stop_saved==!fail_api);
        // Failed stops remain retryable; failed persistence isn't mislabeled saved.
        stop_result=0;service_user_stop(d,running,applied,true,ack);
        assert(ack && file_attempts==1);
    }
    Device empty;s_observe_worker=true;s_user_stopped=false;polls=0;
    assert(check_output_attachment(empty,999999));assert(polls==0 && !s_user_stopped);
    std::cout<<"PASS actual SDL attachment cadence/loss latch/output wrappers; no hardware\n";
    return 0;
}
'''


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--native-source', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    native = args.native_source.read_text(encoding='utf-8')
    device = native[native.index('struct Device\n'):native.index('// Resolve the whole inventory')]
    body = native[native.index('static bool latch_user_stop('):native.index('static void worker()')]
    # The actual worker must invoke the check before its locked output tick and
    # before startup condition effects. This is wiring proof, not a timing claim.
    worker = native[native.index('static void worker()'):native.index('static void shutdown()')]
    assert worker.count('check_output_attachment(d,now_ms());') == 3
    loop = worker[worker.index('while (!s_stop.load()'):]
    assert loop.index('check_output_attachment') < loop.index('std::lock_guard<std::mutex> output_guard')
    assert worker.index('check_output_attachment') < worker.index('int cond_ids[3]')
    assert 'midv_ffb_user_stop()' not in worker
    assert worker.count('service_user_stop(d,running,applied,rumble_ok,user_stop_acknowledged);') == 3
    source = args.output/'disconnect.cpp'
    source.write_text(PREFIX+device+body+SUFFIX, encoding='utf-8')
    compiler = Path('E:/msys64/mingw64/bin/g++.exe')
    env = dict(os.environ, PATH=str(compiler.parent)+os.pathsep+os.environ.get('PATH', ''))
    binary = args.output/'disconnect.exe'
    build = subprocess.run([str(compiler), '-std=c++17', '-O2', '-Wall', '-Wextra', '-static',
        '-I'+str(ROOT/'native'), str(source), '-o', str(binary)], env=env, capture_output=True, text=True, timeout=120)
    (args.output/'build.log').write_text(build.stdout+build.stderr, encoding='utf-8')
    build.check_returncode()
    run = subprocess.run([str(binary)], env=env, capture_output=True, text=True, timeout=30)
    (args.output/'run.log').write_text(run.stdout+run.stderr, encoding='utf-8')
    run.check_returncode()
    receipt = dict(passed=True, physical_output=False,
        native_source_sha256=hashlib.sha256(args.native_source.read_bytes()).hexdigest(),
        extracted_sha256=hashlib.sha256((device+body).encode('utf-8')).hexdigest(),
        test_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest())
    (args.output/'qualified.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
    print(run.stdout)


if __name__ == '__main__':
    main()
