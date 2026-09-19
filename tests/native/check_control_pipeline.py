"""Compile actual MAME absolute-input method with fake input providers."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[2]
PREFIX=r'''
#include <cassert>
#include <cstdint>
#include <cstring>
#include <iostream>
#include "control_calibration.h"
using s32=int32_t;
namespace osd { struct input_device { static constexpr s32 ABSOLUTE_MIN=-65536,ABSOLUTE_MAX=65536; }; }
enum { DEVICE_CLASS_JOYSTICK=1,ITEM_ID_XAXIS=10 };
enum input_item_modifier { ITEM_MODIFIER_NONE,ITEM_MODIFIER_REVERSE,ITEM_MODIFIER_POS,ITEM_MODIFIER_NEG };
void fatalerror(char const *message) { throw std::runtime_error(message); }
using LONG=int32_t;
using input_device=osd::input_device;
constexpr int DI_OK=0;
struct RawState { LONG lX=0,lY=0,lZ=0,lRx=0,lRy=0,lRz=0,slider[2]={};uint32_t rgdwPOV[4]={};unsigned char buttons[128]={}; } next_state;
static bool connected=true;
struct dinput_device {
    int poll_dinput(void *state) { if (!connected) return -1;std::memcpy(state,&next_state,sizeof(next_state));return 0; }
};
struct dinput_joystick_device:dinput_device {
    struct { RawState state;LONG rangemin[8]={},rangemax[8]={65536,65536,65536,65536,65536,65536,65536,65536}; } m_joystick;
    std::string identity="Wheel product_00112233-4455-6677-8899-aabbccddeeff instance_11112233-4455-6677-8899-aabbccddeeff";
    std::string const &id() const { return identity; }
    void reset();void poll(bool relative_reset);
};
struct FakeDevice {
    std::string identity="Wheel product_00112233-4455-6677-8899-aabbccddeeff instance_11112233-4455-6677-8899-aabbccddeeff";
    int adjustments=0;
    int devclass() const { return DEVICE_CLASS_JOYSTICK; }
    std::string const &id() const { return identity; }
    s32 adjust_absolute(s32 raw) { ++adjustments;return raw/2; }
};
struct input_device_absolute_item {
    FakeDevice m_device;s32 raw=0;int axis=0,reads=0;
    int itemid() const { return ITEM_ID_XAXIS+axis; }
    s32 update_value() { ++reads;return raw; }
    s32 read_as_absolute(input_item_modifier modifier);
};
'''
SUFFIX=r'''
int main(int argc,char **argv)
{
    assert(argc==2);_putenv_s("MIDV_INPUT_PROFILE",argv[1]);
    dinput_joystick_device physical;
    physical.reset();assert(physical.m_joystick.state.lX==0 && physical.m_joystick.state.lY==-65536 && physical.m_joystick.state.lZ==-65536);
    next_state.lX=49152;next_state.lY=32768;next_state.lZ=0;next_state.buttons[100]=0x80;
    physical.poll(false);
    assert(physical.m_joystick.state.lX==24576 && physical.m_joystick.state.lY==0 && physical.m_joystick.state.lZ==65536);
    input_device_absolute_item steering;
    steering.raw=physical.m_joystick.state.lX;assert(steering.read_as_absolute(ITEM_MODIFIER_NONE)==24576);
    assert(steering.reads==1 && steering.m_device.adjustments==0);
    steering.raw=70000;assert(steering.read_as_absolute(ITEM_MODIFIER_NONE)==0);
    bool rejected=false;try { steering.read_as_absolute(ITEM_MODIFIER_POS); }catch(std::exception const &) { rejected=true; }assert(rejected);
    input_device_absolute_item pedal;pedal.axis=1;
    pedal.raw=physical.m_joystick.state.lY;assert(pedal.read_as_absolute(ITEM_MODIFIER_NONE)==0); // Half pedal, not the old half-axis release.
    pedal.raw=-65536;assert(pedal.read_as_absolute(ITEM_MODIFIER_NONE)==-65536);
    pedal.raw=65536;assert(pedal.read_as_absolute(ITEM_MODIFIER_NONE)==65536);
    pedal.raw=70000;assert(pedal.read_as_absolute(ITEM_MODIFIER_NONE)==-65536);
    assert(pedal.m_device.adjustments==0);
    connected=false;physical.poll(false);
    assert(physical.m_joystick.state.lX==0 && physical.m_joystick.state.lY==-65536 && physical.m_joystick.state.lZ==-65536);
    assert(physical.m_joystick.state.buttons[100]==0 && physical.m_joystick.state.rgdwPOV[0]==0xffff);
    pedal.raw=physical.m_joystick.state.lY;assert(pedal.read_as_absolute(ITEM_MODIFIER_NONE)==-65536);
    input_device_absolute_item legacy;legacy.axis=3;legacy.raw=32768;
    assert(legacy.read_as_absolute(ITEM_MODIFIER_NONE)==16384);
    assert(legacy.read_as_absolute(ITEM_MODIFIER_POS)==-32768);
    assert(legacy.m_device.adjustments==2);
    legacy.axis=0;legacy.m_device.identity="Other device";
    assert(legacy.read_as_absolute(ITEM_MODIFIER_NONE)==16384);
    std::cout<<"PASS actual MAME input method: calibrated mapping once, invalid neutral, legacy deadzone/half-axis retained\n";
}
'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--native-source',type=Path,required=True)
    parser.add_argument('--dinput-source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    args.output.mkdir(parents=True,exist_ok=False)
    text=args.native_source.read_text(encoding='utf-8')
    first=text.index('s32 input_device_absolute_item::read_as_absolute(input_item_modifier modifier)')
    last=text.index('//-------------------------------------------------',first)
    body=text[first:last]
    backend_text=args.dinput_source.read_text(encoding='utf-8')
    first=backend_text.index('void dinput_joystick_device::reset()')
    last=backend_text.index('void dinput_joystick_device::configure(',first)
    backend=backend_text[first:last]
    source=args.output/'pipeline.cpp';source.write_text(PREFIX+backend+body+SUFFIX,encoding='utf-8')
    binary=args.output/'pipeline.exe';compiler=Path('E:/msys64/mingw64/bin/g++.exe')
    env=dict(os.environ,PATH=str(compiler.parent)+os.pathsep+os.environ.get('PATH',''))
    build=subprocess.run([str(compiler),'-std=c++17','-O2','-Wall','-Wextra','-static','-I'+str(ROOT/'native'),
                          str(source),'-o',str(binary)],env=env,capture_output=True,text=True,timeout=120)
    (args.output/'build.log').write_text(build.stdout+build.stderr,encoding='utf-8');build.check_returncode()
    profile=args.output/'profile.txt'
    identity='00112233-4455-6677-8899-aabbccddeeff|11112233-4455-6677-8899-aabbccddeeff|'
    profile.write_text('cruisn-calibration-v1\n'+identity+'XAXIS|steering|-1|0|1|0|0.2\n'+
                       identity+'YAXIS|pedal|-1|0|1|0|0\n'+identity+'ZAXIS|pedal|-1|0|1|1|0\n',encoding='utf-8')
    run=subprocess.run([str(binary.resolve()),str(profile.resolve())],env=env,capture_output=True,text=True,timeout=30)
    (args.output/'run.log').write_text(run.stdout+run.stderr,encoding='utf-8');run.check_returncode()
    result=dict(passed=True,physical_output=False,scope='Actual method with fake devices; no hardware/ADC acceptance',
                source_sha256=hashlib.sha256(args.native_source.read_bytes()).hexdigest(),
                method_sha256=hashlib.sha256(body.encode('utf-8')).hexdigest(),
                backend_method_sha256=hashlib.sha256(backend.encode('utf-8')).hexdigest(),
                executable_sha256=hashlib.sha256(binary.read_bytes()).hexdigest())
    (args.output/'qualified.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(run.stdout)


if __name__=='__main__':main()
