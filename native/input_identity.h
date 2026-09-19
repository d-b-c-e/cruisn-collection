// Opt-in exact DirectInput mapping. Friendly device names are presentation only.
#pragma once
#include <string>
#include <string_view>
#include <vector>

namespace cruisn {
inline bool input_guid(std::string_view text)
{
	if (text.size()!=36) return false;
	bool nonzero=false;
	for (std::size_t i=0;i<text.size();++i) {
		char const c=text[i];
		if (i==8 || i==13 || i==18 || i==23) { if (c!='-') return false; }
		else if (!((c>='0' && c<='9') || (c>='a' && c<='f') || (c>='A' && c<='F'))) return false;
		else if (c!='0') nonzero=true;
	}
	return nonzero;
}
inline std::string input_identity_fold(std::string_view text)
{
	std::string result(text);
	for (char &c:result) if (c>='a' && c<='z') c=char(c-'a'+'A');
	return result;
}
inline bool strict_input_selector(std::string_view text)
{
	return text.substr(0,14)=="strict-dinput:";
}
inline std::string input_identity_key(std::string_view product,std::string_view instance)
{
	return input_guid(product) && input_guid(instance)?input_identity_fold(product)+":"+input_identity_fold(instance):"";
}
inline std::string requested_input_identity(std::string_view selector)
{
	if (!strict_input_selector(selector)) return "";
	selector.remove_prefix(14);
	if (selector.size()!=73 || selector[36]!=':') return "";
	return input_identity_key(selector.substr(0,36),selector.substr(37));
}
inline std::string actual_input_identity(std::string_view device_id)
{
	// MAME DirectInput make_id appends this exact GUID suffix to the name.
	auto const product=device_id.rfind(" product_");
	if (product==std::string_view::npos) return "";
	device_id.remove_prefix(product+9);
	if (device_id.size()!=82 || device_id.substr(36,10)!=" instance_") return "";
	return input_identity_key(device_id.substr(0,36),device_id.substr(46));
}
inline int unique_input_identity(std::string_view selector,std::vector<std::string> const &device_ids)
{
	std::string const requested=requested_input_identity(selector);
	if (requested.empty()) return -3;
	int selected=-1;
	for (std::size_t i=0;i<device_ids.size();++i) {
		if (actual_input_identity(device_ids[i])!=requested) continue;
		if (selected>=0) return -2;
		selected=int(i);
	}
	return selected;
}
} // namespace cruisn
