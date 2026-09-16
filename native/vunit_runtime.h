// SPDX-License-Identifier: BSD-3-Clause
#pragma once
#include <cstdint>
#include <cstring>
#include <limits>
#include <initializer_list>
namespace cruisn { namespace vunit_runtime {
enum class Policy { capture, continuous };
template<class Lookup> bool select(const char *mode,Lookup lookup,Policy &policy)
{
    policy=Policy::capture;
    if(!mode)return true;
    if(std::strcmp(mode,"continuous"))return false;
    for(const auto *key:{"MIDV_HOST_BOOTSTRAP","MIDV_GL"}) {
        const char *value=lookup(key);if(!value || std::strcmp(value,"1"))return false;
    }
    const char *ffb=lookup("MIDV_FFB");if(!ffb || std::strcmp(ffb,"0"))return false;
    policy=Policy::continuous;return true;
}
inline bool continuous(Policy policy){return policy==Policy::continuous;}
inline bool representable(uint64_t frame){return frame<=std::numeric_limits<uint32_t>::max();}
inline bool after(Policy policy,uint64_t frame,uint32_t last){return !continuous(policy)&&frame>last;}
inline bool within(Policy policy,uint64_t frame,uint32_t first,uint32_t last,bool bootstrap)
{return representable(frame) && (bootstrap||frame>=first) && !after(policy,frame,last);}
}}
