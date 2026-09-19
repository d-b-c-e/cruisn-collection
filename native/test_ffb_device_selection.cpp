#include "ffb_device_selection.h"
#include <cassert>
#include <iostream>

int main()
{
	using namespace cruisn;
	force_device_identity wheel{"Wheel","\\\\?\\hid#one",0x1234,0xabcd,false};
	force_device_identity other{"Wheel Pro","\\\\?\\hid#two",0x1234,0xabcd,false};
	std::vector<force_device_identity> devices{wheel,other};
	assert(select_force_device("",devices).index==-1);
	assert(select_force_device("Whee",devices).index==-1);
	assert(select_force_device("Wheel",devices).index==0);
	assert(select_force_device("name:wheel pro",devices).index==1);
	assert(select_force_device("1234:abcd",devices).index==-1);
	assert(select_force_device("1234:abcd trailing",devices).index==-1);
	assert(select_force_device("11234:abcd",devices).index==-1);
	assert(select_force_device("path:",devices).index==-1);
	assert(select_force_device("path:unverified",devices).index==-1);
	assert(select_force_device("path:\\\\?\\HID#TWO",devices).index==1);
	std::swap(devices[0],devices[1]);
	assert(select_force_device("path:\\\\?\\hid#two",devices).index==0);
	devices[0].name="Wheel";
	assert(select_force_device("Wheel",devices).index==-1);
	assert(select_force_device("path:\\\\?\\hid#one",devices).index==1);
	devices[1].virtual_device=true;
	assert(select_force_device("path:\\\\?\\hid#one",devices).index==-1);
	devices[1].virtual_device=false;devices[1].name="vJoy Device";
	assert(select_force_device("path:\\\\?\\hid#one",devices).index==-1);
	devices[1].name="Wheel";devices[0].path=devices[1].path;
	assert(select_force_device("path:\\\\?\\hid#one",devices).index==-1);
	std::cout<<"PASS exact unique names, instance paths, duplicate/missing/virtual rejection and reorder\n";
}
