// SPDX-License-Identifier: BSD-3-Clause
// A machine reset is an ordered boundary, not completion of pending work.
#pragma once
#include <array>
#include <cstdint>
#include <cstring>
#include <limits>
namespace cruisn { namespace exotica_reset {
struct Request {uint32_t frame=0;uint64_t index=0,scene=0,generation=0,hash=0;};
using Wire=std::array<uint32_t,10>;
inline bool valid(const Request &r) {return r.frame && r.index && ((r.scene!=0)==(r.generation!=0));}
inline Wire encode(const Request &r) {
    return {{0x31535258,r.frame,uint32_t(r.index),uint32_t(r.index>>32),
        uint32_t(r.scene),uint32_t(r.scene>>32),uint32_t(r.generation),uint32_t(r.generation>>32),
        uint32_t(r.hash),uint32_t(r.hash>>32)}};
}
inline bool decode(const void *data,size_t size,Request &out) {
    if(!data || size!=sizeof(Wire))return false;
    Wire w;std::memcpy(w.data(),data,size);if(w[0]!=0x31535258)return false;
    Request r{w[1],uint64_t(w[2])|(uint64_t(w[3])<<32),uint64_t(w[4])|(uint64_t(w[5])<<32),
        uint64_t(w[6])|(uint64_t(w[7])<<32),uint64_t(w[8])|(uint64_t(w[9])<<32)};
    if(!valid(r))return false;
    out=r;return true;
}
// Before the first pool/scene transaction there is no auxiliary ownership to
// invalidate or GPU work to reseed. A caller must also prove phase quiescence.
inline bool pristine(bool pending,bool pool_ready,bool scene_started,bool lifetime_started,
                     uint64_t epoch,uint64_t generation,uint64_t prepared,uint64_t scene,uint64_t resets) {
    return !pending && !pool_ready && !scene_started && !lifetime_started &&
        !epoch && !generation && !prepared && !scene && !resets;
}
// The adapter collects every live phase before touching guest or host state.
inline bool quiescent(uint32_t pending,uint64_t prepared,uint64_t matched,uint64_t requested,
                      uint64_t completed,uint64_t waiting,uint64_t active,uint64_t composed) {
    return !pending && prepared==matched && matched==requested && requested==completed &&
        completed==waiting && waiting==active && active==composed;
}
inline bool gpu_matches(const Request &r,uint64_t previous,uint32_t frame,uint64_t scene,
                        uint64_t late,uint64_t waiting,uint64_t generation,uint64_t hash,bool endpoints_complete) {
    return valid(r) && previous<std::numeric_limits<uint64_t>::max() && r.index==previous+1 &&
        r.frame>=frame && r.scene==scene && scene==late && scene==waiting &&
        r.generation==generation && r.hash==hash && endpoints_complete;
}
// Copy at identical texels. Convert ordinary D24 to the private 26-bit depth
// scale; preserve the all-ones clear code. Never write the ordinary target.
// MAME's makedep lexer does not recognize C++ raw string delimiters. Ordinary
// adjacent literals keep the compiled GLSL bytes identical on project regen.
static const char *const seed_vertex=
    "#version 330 core\n"
    "void main() {\n"
    "    vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);\n"
    "    gl_Position=vec4(p*2.0-1.0,0.0,1.0);\n"
    "}\n";
static const char *const seed_fragment=
    "#version 330 core\n"
    "uniform sampler2D original_color;\n"
    "uniform sampler2D original_depth;\n"
    "out vec4 color;\n"
    "void main() {\n"
    "    ivec2 p=ivec2(gl_FragCoord.xy);\n"
    "    color=texelFetch(original_color,p,0);\n"
    "    uint code=uint(round(texelFetch(original_depth,p,0).r*16777215.0));\n"
    "    gl_FragDepth=code==16777215u?1.0:float(code)*(1.0/67108864.0);\n"
    "}\n";
} }
