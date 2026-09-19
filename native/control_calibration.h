// Versioned, opt-in calibration applied once, before legacy MAME axis modifiers.
#pragma once
#include "input_identity.h"
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <stdexcept>

namespace cruisn {
struct control_calibration {
	bool pedal=false,invert=false;
	double first=0.,centre=0.,last=0.,deadzone=0.;
};
inline void validate_control_calibration(control_calibration const &c)
{
	for (double value:{c.first,c.centre,c.last})
		if (!std::isfinite(value) || value< -1. || value>1.) throw std::runtime_error("Invalid calibration endpoint");
	if (!std::isfinite(c.deadzone) || c.deadzone<0. || c.deadzone>=1.) throw std::runtime_error("Invalid calibration deadzone");
	if (c.pedal) {
		if (std::abs(c.last-c.first)<.05) throw std::runtime_error("Pedal calibration span too small");
	} else {
		if ((c.first-c.centre)*(c.last-c.centre)>=0. || std::abs(c.first-c.centre)<.05 || std::abs(c.last-c.centre)<.05)
			throw std::runtime_error("Invalid steering calibration spans");
	}
}
inline double normalize_control(double raw,control_calibration const &c)
{
	validate_control_calibration(c);
	if (!std::isfinite(raw) || raw< -1. || raw>1.) throw std::runtime_error("Invalid raw calibration sample");
	double value;
	if (c.pedal) value=std::clamp((raw-c.first)/(c.last-c.first),0.,1.);
	else {
		double const displacement=(raw-c.centre)*(c.last>c.centre?1.:-1.);
		value=std::clamp(displacement/std::abs(displacement<0.?c.first-c.centre:c.last-c.centre),-1.,1.);
	}
	if (c.invert) value=c.pedal?1.-value:-value;
	return c.pedal?std::max(0.,(value-c.deadzone)/(1.-c.deadzone)):
		(value<0.?-1.:1.)*std::max(0.,(std::abs(value)-c.deadzone)/(1.-c.deadzone));
}
inline double neutral_control_raw(control_calibration const &c)
{
	return c.pedal?(c.invert?c.last:c.first):c.centre;
}
inline int control_axis_slot(std::string_view name)
{
	char const *names[]={"XAXIS","YAXIS","ZAXIS","RXAXIS","RYAXIS","RZAXIS","SLIDER1","SLIDER2"};
	for (int i=0;i<8;++i) if (name==names[i]) return i;
	return -1;
}
struct control_calibration_entry {
	std::string identity;
	int slot=-1;
	control_calibration calibration;
};
struct control_calibration_profile {
	bool configured=false;
	std::vector<control_calibration_entry> entries;
	control_calibration const *find(std::string_view device_id,int slot) const
	{
		if (!configured || slot<0) return nullptr;
		std::string const key=actual_input_identity(device_id);
		for (auto const &entry:entries) if (entry.identity==key && entry.slot==slot) return &entry.calibration;
		return nullptr;
	}
};
inline control_calibration_profile parse_control_calibration(std::istream &stream)
{
	control_calibration_profile result;result.configured=true;
	std::string line;std::size_t bytes=0;
	if (!std::getline(stream,line)) throw std::runtime_error("Missing calibration header");
	if (!line.empty() && line.back()=='\r') line.pop_back();
	if (line!="cruisn-calibration-v1") throw std::runtime_error("Unsupported calibration schema");
	while (std::getline(stream,line)) {
		bytes+=line.size();
		if (bytes>65536 || line.size()>1024 || result.entries.size()>=128) throw std::runtime_error("Calibration profile bound");
		if (!line.empty() && line.back()=='\r') line.pop_back();
		std::vector<std::string> fields;
		std::size_t begin=0;
		for (;;) {
			auto const end=line.find('|',begin);fields.push_back(line.substr(begin,end==std::string::npos?end:end-begin));
			if (end==std::string::npos) break;
			begin=end+1;
		}
		if (fields.size()!=9) throw std::runtime_error("Calibration profile field count");
		control_calibration_entry entry;
		entry.identity=input_identity_key(fields[0],fields[1]);entry.slot=control_axis_slot(fields[2]);
		if (entry.identity.empty() || entry.slot<0 || (fields[3]!="steering" && fields[3]!="pedal")
			|| (fields[7]!="0" && fields[7]!="1")) throw std::runtime_error("Invalid calibration identity/axis/kind");
		auto number=[&fields](int index) {
			char *end=nullptr;double const value=std::strtod(fields[index].c_str(),&end);
			if (fields[index].empty() || *end || !std::isfinite(value)) throw std::runtime_error("Invalid calibration number");
			return value;
		};
		entry.calibration={fields[3]=="pedal",fields[7]=="1",number(4),number(5),number(6),number(8)};
		validate_control_calibration(entry.calibration);
		for (auto const &prior:result.entries) if (prior.identity==entry.identity && prior.slot==entry.slot)
			throw std::runtime_error("Duplicate calibration for one device axis");
		result.entries.push_back(entry);
	}
	if (stream.bad()) throw std::runtime_error("Could not read calibration profile");
	return result;
}
inline control_calibration_profile const &active_control_calibration()
{
	static control_calibration_profile const profile=[] {
#ifdef _WIN32
		wchar_t const *path=_wgetenv(L"MIDV_INPUT_PROFILE");
#else
		char const *path=std::getenv("MIDV_INPUT_PROFILE");
#endif
		if (!path) return control_calibration_profile{};
		if (!*path) throw std::runtime_error("Empty calibration profile path");
		std::filesystem::path const filename(path);
		if (std::filesystem::file_size(filename)>65536) throw std::runtime_error("Calibration file byte bound");
		std::ifstream stream(filename);
		if (!stream) throw std::runtime_error("Cannot open calibration profile");
		return parse_control_calibration(stream);
	}();
	return profile;
}
} // namespace cruisn
