// SPDX-License-Identifier: BSD-3-Clause
#include "exotica_journal_policy.h"
#include <cassert>
#include <map>
#include <string>
int main() {
    using Policy=cruisn::DiagnosticJournal::Policy;
    std::map<std::string,std::string> env={
        {"MIDV_FFB","0"},{"MIDZ_GL","1"},{"MIDZ_HOST_SCENE","1"},
        {"MIDZ_LIFETIME","1"},{"MIDZ_HOST_MATERIALS","1"},
        {"MIDZ_HOST_WAITING","1"},{"MIDZ_HOST_FENCE","1"},
        {"MIDZ_HOST_HANDOVER","2"},{"MIDZ_HOST_ACTIVE","2"},
        {"MIDZ_HOST_COMPOSE","1"},{"MIDZ_HOST_FUTURE","2"},
        {"MIDZ_HOST_FUTURE_PRESENT","1"},{"MIDZ_DEPTH_MIRROR","2"},
        {"MIDZ_MODEL_ENDPOINT","2"},{"MIDZ_ENDPOINT_EARLY","1"},
        {"MIDZ_ENDPOINT_MARKED","1"}};
    auto lookup=[&](const char *key)->const char * {
        auto it=env.find(key);return it==env.end()?nullptr:it->second.c_str();
    };
    Policy policy=Policy::quiet;
    assert(cruisn::exotica_journals::select(nullptr,lookup,policy) && policy==Policy::capture);
    assert(cruisn::exotica_journals::select("capture",lookup,policy) && policy==Policy::capture);
    assert(cruisn::exotica_journals::select("quiet",lookup,policy) && policy==Policy::quiet);
    for(const char *bad:{"","0","1","Quiet","quiet ","other"})
        assert(!cruisn::exotica_journals::select(bad,lookup,policy));
    const auto saved=env;
    for(const auto &entry:saved) {
        env=saved;env.erase(entry.first);
        assert(!cruisn::exotica_journals::select("quiet",lookup,policy));
        env[entry.first]="invalid";
        assert(!cruisn::exotica_journals::select("quiet",lookup,policy));
    }
    env.clear();assert(cruisn::exotica_journals::select("capture",lookup,policy));
}
