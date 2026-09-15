// SPDX-License-Identifier: BSD-3-Clause
#include "exotica_runtime.h"
#include <cassert>
#include <map>
#include <string>
int main() {
    using namespace cruisn::exotica_runtime;
    std::map<std::string,std::string> env={
        {"MIDV_FFB","0"},{"MIDZ_GL","1"},{"MIDZ_HOST_SCENE","1"},
        {"MIDZ_LIFETIME","1"},{"MIDZ_HOST_MATERIALS","1"},{"MIDZ_HOST_WAITING","1"},
        {"MIDZ_HOST_FENCE","1"},{"MIDZ_HOST_HANDOVER","2"},{"MIDZ_HOST_ACTIVE","2"},
        {"MIDZ_HOST_COMPOSE","1"},{"MIDZ_HOST_FUTURE","2"},{"MIDZ_HOST_FUTURE_PRESENT","1"},
        {"MIDZ_DEPTH_MIRROR","2"},{"MIDZ_MODEL_ENDPOINT","2"},{"MIDZ_ENDPOINT_EARLY","1"},
        {"MIDZ_ENDPOINT_MARKED","1"},{"MIDZ_HOST_JOURNALS","quiet"},
        {"MIDZ_BOOTSTRAP","3"},{"MIDZ_SHUTDOWN_OBSERVE","1"},{"MIDZ_DEPTH_FIRST","2"}};
    auto lookup=[&](const char *key)->const char * {auto it=env.find(key);return it==env.end()?nullptr:it->second.c_str();};
    Policy policy=Policy::continuous;
    assert(select(nullptr,lookup,policy) && policy==Policy::capture);
    assert(select("continuous",lookup,policy) && continuous(policy));
    for(const char *bad:{"","1","Continuous","continuous ","capture"})assert(!select(bad,lookup,policy));
    const auto saved=env;
    for(const auto &entry:saved) {
        env=saved;env.erase(entry.first);assert(!select("continuous",lookup,policy));
        env[entry.first]="bad";assert(!select("continuous",lookup,policy));
    }
    for(uint64_t frame:{1ull,1799ull,1800ull,5200ull,5201ull,16002ull,1000000ull,4294967295ull}) {
        assert(within(Policy::continuous,frame,1800,5200)==(frame>=1800));
        assert(within(Policy::capture,frame,1800,5200)==(frame>=1800 && frame<=5200));
    }
    assert(!representable(4294967296ull));
    assert(!within(Policy::continuous,4294967296ull,1800,5200));
}
