#include "vunit_runtime.h"
#include <cassert>
#include <map>
#include <string>
int main()
{
 using namespace cruisn::vunit_runtime;
 std::map<std::string,std::string> values={{"MIDV_HOST_BOOTSTRAP","1"},{"MIDV_GL","1"},{"MIDV_FFB","0"}};
 auto lookup=[&](const char *key)->const char*{auto it=values.find(key);return it==values.end()?nullptr:it->second.c_str();};
 Policy policy;
 assert(select(nullptr,lookup,policy)&&policy==Policy::capture);
 assert(!within(policy,99,100,200,false));assert(within(policy,99,100,200,true));
 assert(within(policy,200,100,200,true));assert(!within(policy,201,100,200,true));
 assert(select("continuous",lookup,policy)&&policy==Policy::continuous);
 for(uint64_t frame:{201ull,1000001ull,4294967295ull})assert(within(policy,frame,100,200,true));
 assert(!within(policy,4294967296ull,100,200,true));
 assert(!select("capture",lookup,policy));
 for(auto &entry:values){auto old=entry.second;entry.second="invalid";assert(!select("continuous",lookup,policy));entry.second=old;}
 values.erase("MIDV_HOST_BOOTSTRAP");assert(!select("continuous",lookup,policy));
}
