// SPDX-License-Identifier: BSD-3-Clause
#include "exotica_reset.h"
#include <cassert>
int main() {
    using namespace cruisn::exotica_reset;
    assert(std::strlen(seed_vertex)==126 && std::strlen(seed_fragment)==335);
    Request r{18001,3,75000,225000,0xfedcba9876543210ull},out;
    auto wire=encode(r);assert(decode(wire.data(),sizeof(wire),out));
    assert(out.frame==r.frame && out.index==r.index && out.scene==r.scene && out.generation==r.generation && out.hash==r.hash);
    assert(!decode(wire.data(),sizeof(wire)-1,out));
    wire[0]^=1;assert(!decode(wire.data(),sizeof(wire),out));
    assert(quiescent(0,4,4,4,4,4,4,4));assert(quiescent(0,0,0,0,0,0,0,0));
    for(unsigned bit=0;bit<32;++bit)assert(!quiescent(1u<<bit,4,4,4,4,4,4,4));
    for(unsigned i=0;i<7;++i) {
        uint64_t a[]={4,4,4,4,4,4,4};a[i]++;
        assert(!quiescent(0,a[0],a[1],a[2],a[3],a[4],a[5],a[6]));
    }
    assert(pristine(false,false,false,false,0,0,0,0,0));
    for(unsigned i=0;i<9;++i) {
        uint64_t a[]={0,0,0,0,0,0,0,0,0};a[i]=1;
        assert(!pristine(a[0],a[1],a[2],a[3],a[4],a[5],a[6],a[7],a[8]));
    }
    assert(gpu_matches(r,2,18000,75000,75000,75000,225000,r.hash,true));
    assert(!gpu_matches(r,3,18000,75000,75000,75000,225000,r.hash,true));
    assert(!gpu_matches(r,2,18002,75000,75000,75000,225000,r.hash,true));
    assert(!gpu_matches(r,2,18000,75000,74999,75000,225000,r.hash,true));
    assert(!gpu_matches(r,2,18000,75000,75000,74999,225000,r.hash,true));
    assert(!gpu_matches(r,2,18000,75000,75000,75000,225001,r.hash,true));
    assert(!gpu_matches(r,2,18000,75000,75000,75000,225000,r.hash^1,true));
    assert(!gpu_matches(r,2,18000,75000,75000,75000,225000,r.hash,false));
    assert(!valid(Request{0,1,0,0,0}));assert(!valid(Request{1,0,0,0,0}));
    assert(!valid(Request{1,1,1,0,0}));assert(!valid(Request{1,1,0,1,0}));
}
