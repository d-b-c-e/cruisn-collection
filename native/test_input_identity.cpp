#include "input_identity.h"
#include <cassert>
#include <iostream>

int main()
{
	std::string product="00112233-4455-6677-8899-AABBCCDDEEFF",one="11112233-4455-6677-8899-AABBCCDDEEFF",two="22112233-4455-6677-8899-AABBCCDDEEFF";
	std::string const requested="strict-dinput:"+product+":"+one;
	std::string const suffix=" product_"+product+" instance_";
	std::vector<std::string> devices{"Wheel"+suffix+one,"Wheel"+suffix+two};
	assert(cruisn::unique_input_identity(requested,devices)==0);
	std::swap(devices[0],devices[1]);
	assert(cruisn::unique_input_identity(requested,devices)==1);
	devices[1]="Renamed device"+suffix+one;
	assert(cruisn::unique_input_identity(requested,devices)==1);
	devices[0]=devices[1];assert(cruisn::unique_input_identity(requested,devices)==-2);
	devices.clear();assert(cruisn::unique_input_identity(requested,devices)==-1);
	devices={"Wheel"+suffix+two};assert(cruisn::unique_input_identity(requested,devices)==-1);
	assert(cruisn::unique_input_identity(requested+"junk",devices)==-3);
	assert(cruisn::unique_input_identity("strict-dinput:"+product+":bad",devices)==-3);
	assert(cruisn::unique_input_identity("Wheel",devices)==-3);
	devices={"Wheel"+suffix+one+"junk"};assert(cruisn::unique_input_identity(requested,devices)==-1);
	std::cout<<"PASS strict DirectInput instance matching: twins/reorder/rename/missing/malformed\n";
}
