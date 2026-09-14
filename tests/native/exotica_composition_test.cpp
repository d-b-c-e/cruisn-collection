// SPDX-License-Identifier: BSD-3-Clause
#include "exotica_composition.h"
#include <cassert>
#include <iostream>
int main() {
    using namespace cruisn;
    std::vector<uint8_t> proposal(zeus_lease::wave_bytes),ready(proposal);
    exotica_scene::Result active,waiting,out;
    zeus_model::Quad q{};q.state[1]=3;q.state[4]=16;q.state[9]=8;
    for(auto &v:q.vertices)v[5]=1;
    q.vertices[1][3]=256;q.vertices[2][4]=256;
    exotica_scene::Instance a;a.entry=0xbbb5;a.source=0x1000;a.palette=1024;a.quad_count=1;
    active.instances={a,a,a};active.instances[1].source=0x1100;active.instances[1].first_quad=1;
    active.instances[2].source=0x1200;active.instances[2].first_quad=2;
    active.quads={q,q,q};active.quads[2].state[5]=123;
    auto b=active.instances[1];b.entry=0xa01000;b.source=0xa02000;b.first_quad=0;
    waiting.instances={b};waiting.quads={q};
    scenery_lifetimes::Handle h;h.slot=0x1100;h.epoch=1;h.generation=2;h.key.realm=4;h.key.section=b.entry;h.key.source=b.source;
    std::vector<scenery_lifetimes::Handle> owners{h};exotica_composition::Counts counts;
    auto run=[&](){return exotica_composition::filter(active,waiting,owners,proposal.data(),ready.data(),ready.size(),out,counts);};
    assert(run() && counts.overlaps==1 && counts.removed_quads==1 && out.instances.size()==2 && out.quads.size()==2);
    assert(out.instances[0].source==0x1000 && out.instances[1].source==0x1200 && out.instances[1].first_quad==1 && out.quads[1].state[5]==123);
    auto reject=[&](){counts.overlaps=999;out.selected=999;assert(!run() && counts.overlaps==999 && out.selected==999);};
    waiting.quads[0].state[7]=8;reject();waiting.quads[0]=q; // Intrinsic alpha is part of identity.
    waiting.quads[0].vertices[0][0]=1;reject();waiting.quads[0]=q;
    waiting.instances[0].descriptor=1;reject();waiting.instances[0]=b;
    ready[0]=1;reject();ready[0]=0; // Covered texture page.
    ready[a.palette*8]=1;reject();ready[a.palette*8]=0;
    ready[16000000]=1;assert(run());ready[16000000]=0; // Unrelated bytes may advance.
    owners[0].key.source++;reject();owners[0]=h;
    owners[0].generation=0;reject();owners[0]=h;
    owners.push_back(h);reject();owners.pop_back();
    auto extra=h;extra.slot++;extra.key.source++;extra.key.realm++;owners.push_back(extra);reject();owners.pop_back();
    extra.key.realm=h.key.realm;extra.epoch++;owners.push_back(extra);reject();owners.pop_back();
    active.instances[1].first_quad=0;reject();active.instances[1].first_quad=1;
    active.instances[2].source=0x1000;reject();active.instances[2].source=0x1200;
    waiting.instances.clear();reject();waiting.instances={b}; // Orphaned geometry.
    waiting.instances[0].quad_count=0;waiting.quads.clear();reject();
    active.instances[1].quad_count=0;active.quads.erase(active.quads.begin()+1);active.instances[2].first_quad=1;
    assert(run() && counts.overlaps==1 && counts.removed_quads==0 && out.quads.size()==2);
    waiting.instances.clear();owners.clear();assert(run() && counts.overlaps==0 && out.instances.size()==3);
    active={};assert(run() && out.instances.empty() && out.quads.empty());
    std::cout<<"PASS composition overlap, order, alpha, materials, identity ambiguity, bounds and transactional rejection\n";
}
