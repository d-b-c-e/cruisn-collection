// SPDX-License-Identifier: BSD-3-Clause
// Private original-model endpoint preparation. No guest writes or GPU calls.
// The caller must establish admitted source/generation, the exact device model
// boundary, resource ownership and one replacement at the original command slot.
#pragma once
#include "exotica_fade.h"
#include "exotica_state.h"
#include "zeus_state.h"
#include "zeus_model.h"

namespace cruisn { namespace exotica_endpoint {
struct Result {
    std::vector<zeus_model::Quad> original,replacement;
    size_t changed=0;
};
inline zeus_model::Context model_context(const zeus_state::Context &c,uint32_t frame) {
    zeus_model::Context m;m.frame=frame;m.quad_size=c.quad_size;m.texture=c.texture;m.yscale=c.yscale;
    m.matrix=c.matrix;std::copy_n(c.translation.begin(),3,m.translation.begin());
    m.regs=c.regs;m.render=c.render;return m;
}
inline bool same_quads(const std::vector<zeus_model::Quad> &a,const std::vector<zeus_model::Quad> &b) {
    return a.size()==b.size() && (a.empty() || !std::memcmp(a.data(),b.data(),a.size()*sizeof(a[0])));
}
// Model words are owned current-device bytes, not a later WaveRAM reconstruction.
// Endpoint mode is deliberately limited to the existing legacy decoding policy.
// Reconstruct an unchanged control first: inherited state must reproduce exactly.
inline bool prepare(const zeus_state::Context &current,uint32_t frame,uint32_t base,uint32_t count,
    uint32_t render_policy,const std::vector<uint32_t> &words,const exotica_state::Operands &operands,Result &result)
{
    if(!zeus_state::valid(current) || !frame || render_policy || !base || count>0xc800 ||
        words.size()!=2*(size_t(count)+1) || !(operands.flags&0x04000000))return false;
    const uint64_t block=(base%1024)+((base>>16)%2048)*1024;
    if(block*2+words.size()>4*1024*1024)return false;
    ExoticaFadeStep finished;
    if(!exotica_finish_marked_fade(operands.object[16],operands.flags,finished) || !finished.completed)return false;
    zeus_model::Result original;
    if(!zeus_model::decode(words,model_context(current,frame),original))return false;
    // Reuse the actual device palette, just as the paired original draw does.
    // Register40 is the most recent transfer (possibly a program), not a
    // persistent palette-load descriptor. Reissuing setup must not infer that
    // an already resident palette needs a different upload from that register.
    const uint32_t palette=operands.object[18]%1024+((operands.object[18]>>16)%2048)*1024;
    if(palette!=current.palette)return false;
    auto input=operands;input.cache.fill(UINT32_MAX);input.cache[0]=input.object[18];
    Result out;out.original=std::move(original.quads);
    bool original_light=false;
    for(unsigned endpoint=0;endpoint<2;++endpoint) {
        if(endpoint){input.object[16]=finished.packed;input.flags=finished.flags;}
        exotica_state::Result setup;zeus_state::Result state;zeus_model::Result decoded;
        if(!exotica_state::setup(input,setup) || !zeus_state::transition(current,{},setup.packet,base,state))return false;
        const auto &c=state.context;
        if(!endpoint)original_light=setup.branch==exotica_state::Branch::Light && setup.program==3;
        // Exotica's marked static-light fade completes from 29b to 22b. Both
        // use the same 12-word model format and no z offset in the current
        // renderer. This private decoder does not execute/upload microcode;
        // require the exact known transition, then prove every output vertex
        // and material unchanged below. Other program changes still fail.
        const bool light_completion=endpoint && original_light && setup.program==2 &&
            current.ucode==0x29b && c.ucode==0x22b && current.quad_size==12;
        if(c.quad_size!=current.quad_size || (c.ucode!=current.ucode && !light_completion) || c.palette!=current.palette ||
            c.texture!=current.texture || c.yscale!=current.yscale || c.matrix!=current.matrix ||
            c.translation!=current.translation)return false;
        // No palette upload is allowed: source identity and the existing GPU
        // binding are preserved. Only the checked program request is simulated.
        for(const auto &load:state.loads) {
            if(load.kind==5) {if(load.source!=current.ucode && !(light_completion && load.source==c.ucode))return false;}
            else return false;
        }
        if(!zeus_model::decode(words,model_context(c,frame),decoded))return false;
        if(!endpoint) {if(!same_quads(out.original,decoded.quads))return false;}
        else out.replacement=std::move(decoded.quads);
    }
    if(out.original.size()!=out.replacement.size())return false;
    for(size_t i=0;i<out.original.size();++i) {
        const auto &a=out.original[i],&b=out.replacement[i];
        if(std::memcmp(a.vertices.data(),b.vertices.data(),sizeof(a.vertices)) || (a.state[9]^b.state[9])&~uint32_t(18))return false;
        for(unsigned j=0;j<17;++j)if((j<7 || j>10) && a.state[j]!=b.state[j])return false;
        out.changed+=std::memcmp(&a,&b,sizeof(a))!=0;
    }
    result=std::move(out);return true;
}
} }
