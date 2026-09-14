// SPDX-License-Identifier: BSD-3-Clause
#include "exotica_scene_endpoint.h"
#include <cassert>
#include <iostream>
using namespace cruisn;
int main() {
    exotica_scene::Result original;
    for(unsigned n=0;n<3;++n) {
        exotica_scene::Instance i;i.entry=0xbbb5;i.source=0x1000+n*32;
        i.first_quad=n;i.quad_count=1;i.base=10+n;
        original.instances.push_back(i);
        zeus_model::Quad q{};q.state[0]=2000;q.state[1]=4;
        q.state[7]=64+n;q.state[8]=192-n;q.state[9]=2;q.state[10]=8;
        q.vertices[0][0]=float(n);original.quads.push_back(q);
    }
    auto endpoint=original;endpoint.quads[0].state[7]=255;endpoint.quads[0].state[8]=0;
    endpoint.quads[0].state[9]=0;endpoint.quads[0].state[10]=0;
    original.quads[0].state[9]|=16; // actual flag0x200 endpoint disables depth writing
    // The third source is intrinsically transparent; its caller did not mark it.
    auto retained=original;retained.instances.erase(retained.instances.begin()+1);
    retained.quads.erase(retained.quads.begin()+1);retained.instances[1].first_quad=1;
    exotica_scene::Result output;
    assert(exotica_scene_endpoint::select(original,endpoint,retained,true,output));
    assert(output.quads[0].state[7]==255 && output.quads[1].state==original.quads[2].state);
    const auto saved=output.quads;
    auto reject=[&](const exotica_scene::Result &a,const exotica_scene::Result &b,const exotica_scene::Result &r) {
        assert(!exotica_scene_endpoint::select(a,b,r,true,output));
        assert(output.quads.size()==saved.size() && !std::memcmp(output.quads.data(),saved.data(),saved.size()*sizeof(saved[0])));
    };
    auto bad=endpoint;bad.quads[1].vertices[0][0]+=1;reject(original,bad,retained); // even removed geometry is validated
    bad=endpoint;bad.quads[0].state[2]^=1;reject(original,bad,retained);
    bad=endpoint;bad.quads[0].state[9]^=4;reject(original,bad,retained);
    bad=endpoint;bad.quads[0].state[9]^=8;reject(original,bad,retained); // depth testing must stay fixed
    bad=endpoint;bad.instances[0].base++;reject(original,bad,retained);
    bad=retained;bad.quads[0].state[7]++;reject(original,endpoint,bad); // completed alpha must not hide this
    bad=retained;std::swap(bad.instances[0].source,bad.instances[1].source);reject(original,endpoint,bad);
    bad=retained;bad.instances[1].source=bad.instances[0].source;reject(original,endpoint,bad);
    bad=retained;bad.instances[1].first_quad=99;reject(original,endpoint,bad);
    exotica_scene::Result empty;assert(exotica_scene_endpoint::select(original,endpoint,empty,true,output) && output.quads.empty());
    assert(exotica_scene_endpoint::select(original,endpoint,original,false,output) && output.quads.size()==3);
    std::cout<<"PASS original subset integrity, endpoint state restriction, order and transactional rejection\n";
}
