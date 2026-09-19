// Exact, unique device selection before opening a haptic actuator.
// Legacy name/VID:PID selectors are compatibility selectors, not instance IDs.
#pragma once
#include <string>
#include <vector>

namespace cruisn {
struct force_device_identity {
	std::string name, path;
	unsigned vendor=0, product=0;
	bool virtual_device=false;
};
struct force_device_selection {
	int index=-1;
	char const *reason="No FFB device selected";
};
inline std::string force_identity_fold(std::string value)
{
	for (char &c:value) if (c>='a' && c<='z') c=char(c-'a'+'A');
	return value;
}
inline bool force_hex_word(std::string const &text,unsigned &value)
{
	if (text.empty() || text.size()>4) return false;
	value=0;
	for (char c:force_identity_fold(text)) {
		unsigned digit=c>='0' && c<='9'?unsigned(c-'0'):c>='A' && c<='F'?unsigned(c-'A'+10):16;
		if (digit==16) return false;
		value=value*16+digit;
	}
	return true;
}
inline force_device_selection select_force_device(std::string const &selector,
	std::vector<force_device_identity> const &devices)
{
	force_device_selection result;
	if (selector.empty()) return result;
	if (selector.size()>2048 || selector.find_first_of("\r\n")!=std::string::npos) {
		result.reason="Invalid FFB device selector";return result;
	}
	enum { NAME, PATH, VIDPID } kind=NAME;
	std::string requested=selector;
	unsigned vendor=0,product=0;
	if (requested.compare(0,5,"path:")==0) { kind=PATH;requested.erase(0,5); }
	else if (requested.compare(0,5,"name:")==0) requested.erase(0,5);
	else if (requested.find(':')!=std::string::npos) {
		kind=VIDPID;
		std::size_t const colon=requested.find(':');
		if (!force_hex_word(requested.substr(0,colon),vendor) || !force_hex_word(requested.substr(colon+1),product)) {
			result.reason="Invalid FFB VID:PID selector";return result;
		}
	}
	if (requested.empty() || (kind==PATH && requested.compare(0,4,"\\\\?\\")!=0)) {
		result.reason="Invalid FFB device selector";return result;
	}
	requested=force_identity_fold(requested);
	int match=-1;
	for (std::size_t i=0;i<devices.size();++i) {
		auto const &device=devices[i];
		bool const same=kind==PATH?force_identity_fold(device.path)==requested:
			kind==NAME?force_identity_fold(device.name)==requested:device.vendor==vendor && device.product==product;
		if (!same) continue;
		if (match>=0) { result.reason="FFB device selection is ambiguous";return result; }
		match=int(i);
	}
	if (match<0) { result.reason="Selected FFB device is missing";return result; }
	auto const &device=devices[match];
	std::string const name=force_identity_fold(device.name);
	if (device.virtual_device || name.find("VJOY")!=std::string::npos || name.find("VIGEM")!=std::string::npos
		|| name.find("VXBOX")!=std::string::npos || name.find("XOUTPUT")!=std::string::npos) {
		result.reason="Virtual device cannot own FFB";return result;
	}
	result.index=match;result.reason="Exact unique FFB device";return result;
}
} // namespace cruisn
