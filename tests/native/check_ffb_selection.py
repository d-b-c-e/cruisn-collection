"""Compile the actual native selector with fake SDL: no joystick/haptic devices.

This verifies the dispatch boundary as well as the pure selection policy.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]

PREFIX = r'''
#include <atomic>
#include <cassert>
#include <cstdlib>
#include <string>
#include <vector>
#include <iostream>
#include "ffb_device_selection.h"
using Sint32=int;
enum { SDL_TRUE=1, SDL_JOYSTICK_TYPE_WHEEL=2, SDL_HAPTIC_CONSTANT=4 };
struct SDL_Joystick { int index; } joystick;
struct SDL_Haptic {} haptic;
struct Device { SDL_Joystick *js=nullptr;SDL_Haptic *hp=nullptr;unsigned caps=0;bool is_wheel=false;std::string name;Sint32 instance=-1;std::string path; };
static std::atomic<bool> s_user_stopped{false};
static std::vector<cruisn::force_device_identity> devices;
static int locks=0,joystick_opens=0,haptic_opens=0,joystick_closes=0,haptic_closes=0;
static bool attached=true,changed_instance=false,changed_path=false;
static bool inventory_error=false,opened_error=false;
static unsigned capabilities=SDL_HAPTIC_CONSTANT;
void flog(char const *,...) {}
void osd_printf_info(char const *,...) {}
void p_SDL_LockJoysticks() { ++locks; }
void p_SDL_UnlockJoysticks() { --locks; }
int p_SDL_NumJoysticks() { return int(devices.size()); }
char const *p_SDL_JoystickNameForIndex(int i) { return devices[i].name.c_str(); }
char const *p_SDL_JoystickPathForIndex(int i) { return devices[i].path.c_str(); }
unsigned p_SDL_JoystickGetDeviceVendor(int i) { return devices[i].vendor; }
unsigned p_SDL_JoystickGetDeviceProduct(int i) { return devices[i].product; }
Sint32 p_SDL_JoystickGetDeviceInstanceID(int i) { return inventory_error?-1:i+100; }
int p_SDL_JoystickIsVirtual(int i) { return devices[i].virtual_device; }
SDL_Joystick *p_SDL_JoystickOpen(int i) { assert(locks==1);++joystick_opens;joystick.index=i;return &joystick; }
void p_SDL_JoystickClose(SDL_Joystick *) { ++joystick_closes; }
char const *p_SDL_JoystickName(SDL_Joystick *j) { return devices[j->index].name.c_str(); }
char const *p_SDL_JoystickPath(SDL_Joystick *j) { return changed_path?"\\\\?\\hid#replacement":devices[j->index].path.c_str(); }
unsigned p_SDL_JoystickGetVendor(SDL_Joystick *j) { return devices[j->index].vendor; }
unsigned p_SDL_JoystickGetProduct(SDL_Joystick *j) { return devices[j->index].product; }
bool p_SDL_JoystickGetAttached(SDL_Joystick *) { return attached; }
Sint32 p_SDL_JoystickInstanceID(SDL_Joystick *j) { return opened_error?-1:j->index+(changed_instance?200:100); }
SDL_Haptic *p_SDL_HapticOpenFromJoystick(SDL_Joystick *) { ++haptic_opens;return &haptic; }
void p_SDL_HapticClose(SDL_Haptic *) { ++haptic_closes; }
unsigned p_SDL_HapticQuery(SDL_Haptic *) { return capabilities; }
int p_SDL_JoystickGetType(SDL_Joystick *) { return SDL_JOYSTICK_TYPE_WHEEL; }
char const *p_SDL_GetError() { return "fake"; }
'''

SUFFIX = r'''
static void reset(char const *selector)
{
    _putenv_s("MIDV_FFB_DEVICE",selector);
    devices={{"Wheel","\\\\?\\hid#one",0x1234,0xabcd,false},{"Wheel Pro","\\\\?\\hid#two",0x1234,0xabcd,false}};
    locks=joystick_opens=haptic_opens=joystick_closes=haptic_closes=0;
    attached=true;changed_instance=changed_path=false;s_user_stopped=false;capabilities=SDL_HAPTIC_CONSTANT;
    inventory_error=opened_error=false;
}
int main()
{
    Device d;
    for (auto selector:{"","Whee","Missing","1234:abcd","1234:abcd junk","11234:abcd","path:bad"}) {
        reset(selector);assert(!select_device(d));assert(joystick_opens==0 && haptic_opens==0 && locks==0);
    }
    reset("Wheel");devices[1].name="Wheel";assert(!select_device(d));assert(joystick_opens==0 && haptic_opens==0);
    for (auto name:{"vXbox","XOutput"}) {
        reset(name);devices[0].name=name;assert(!select_device(d));assert(joystick_opens==0 && haptic_opens==0);
    }
    reset("Xbox Controller");devices[0].name="Xbox Controller";assert(select_device(d));assert(haptic_opens==1);
    for (int mode=1;mode<=3;++mode) {
        reset("Wheel");inventory_error=(mode&1)!=0;opened_error=(mode&2)!=0;
        assert(!select_device(d));assert(haptic_opens==0);
        assert(inventory_error?joystick_opens==0:joystick_closes==1);
    }
    reset("path:\\\\?\\hid#one");devices[0].virtual_device=true;assert(!select_device(d));assert(haptic_opens==0 && joystick_opens==0);
    reset("path:\\\\?\\hid#one");attached=false;assert(!select_device(d));assert(haptic_opens==0 && joystick_closes==1);
    reset("path:\\\\?\\hid#one");changed_instance=true;assert(!select_device(d));assert(haptic_opens==0 && joystick_closes==1);
    reset("path:\\\\?\\hid#one");changed_path=true;assert(!select_device(d));assert(haptic_opens==0 && joystick_closes==1);
    reset("Wheel");s_user_stopped=true;assert(!select_device(d));assert(haptic_opens==0 && joystick_opens==0);
    reset("Wheel");capabilities=0;assert(!select_device(d));assert(haptic_opens==1 && haptic_closes==1 && joystick_closes==1);
    reset("Wheel");assert(select_device(d));assert(haptic_opens==1 && joystick_opens==1 && locks==0);
    reset("path:\\\\?\\hid#one");devices[0].name=devices[1].name="Twin";std::swap(devices[0],devices[1]);
    assert(select_device(d));assert(d.js->index==1 && haptic_opens==1 && locks==0);
    std::cout<<"PASS actual native selector: rejected identities open no actuator; disappearance/replacement/reorder checked\n";
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-source', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    original = args.native_source.read_text(encoding='utf-8')
    first = original.index('static bool select_device(Device &d)')
    last = next(original.index(marker, first) for marker in ('static bool latch_user_stop(', '// Sole output-owner thread', 'static void apply(Device &d') if marker in original[first:])
    body = original[first:last]
    source = args.output/'selector.cpp'
    source.write_text(PREFIX + body + SUFFIX, encoding='utf-8')
    binary = args.output/'selector.exe'
    compiler = Path('E:/msys64/mingw64/bin/g++.exe')
    env = dict(os.environ, PATH=str(compiler.parent)+os.pathsep+os.environ.get('PATH', ''))
    build = subprocess.run([str(compiler), '-std=c++17', '-O2', '-Wall', '-Wextra', '-static',
                            '-I'+str(ROOT/'native'), str(source), '-o', str(binary)], env=env,
                           capture_output=True, text=True, timeout=120)
    (args.output/'build.log').write_text(build.stdout+build.stderr, encoding='utf-8')
    build.check_returncode()
    run = subprocess.run([str(binary)], env=env, capture_output=True, text=True, timeout=30)
    (args.output/'run.log').write_text(run.stdout+run.stderr, encoding='utf-8')
    run.check_returncode()
    result = dict(passed=True, physical_output=False, source_sha256=hashlib.sha256(args.native_source.read_bytes()).hexdigest(),
                  selector_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest(),
                  helper_sha256=hashlib.sha256((ROOT/'native/ffb_device_selection.h').read_bytes()).hexdigest(),
                  executable_sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
    (args.output/'qualified.json').write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(run.stdout)


if __name__ == '__main__':
    main()
