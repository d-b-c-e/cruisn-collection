// SPDX-License-Identifier: BSD-3-Clause
#include "exotica_model_endpoint.h"
#include <cassert>
#include <iostream>
#include <limits>
using namespace cruisn;
uint32_t bits(float f){uint32_t w;std::memcpy(&w,&f,4);return w;}
int main()
{
    exotica_state::Operands a;
    auto w=[&](unsigned address,uint32_t value){a.commands[address-0xb479]=value;};
    w(0xb47b,0x32000000);w(0xb47c,0x1c000000);w(0xb481,0x05410000);w(0xb482,0x05400000);
    w(0xb493,0x05200000);w(0xb498,0x14004000);w(0xb499,0x14004062);w(0xb49d,0x15000000);
    w(0xb4a0,0x40020202);w(0xb4a4,0x0c000000);w(0xb4a6,0x0d000000);
    a.constants[2]=0xc700;a.constants[6]=0x8100;
    for(unsigned i=0;i<4;++i){a.programs[i]=i+10;a.bodies[i]={{0x05410000,0xc0,0x05400000,0x38550075}};}
    a.defaults={0x40000000,0x14004000};a.palette_setup=0x0084003f;
    a.flags=0x04000130;a.object[15]=a.flags;a.object[16]=0x78081234;a.object[18]=0x10001;a.cache.fill(UINT32_MAX);
    zeus_state::Context seed;seed.regs[0x66]=0x8e;seed.regs[0x68]=0x9d;seed.regs[0x6c]=9;
    seed.regs[0x6a]=bits(256);seed.regs[0x6b]=bits(200);seed.render[1]=511;seed.render[2]=399;
    seed.matrix={{1,0,0,0,1,0,0,0,1}};seed.translation[2]=100;
    exotica_state::Result setup;zeus_state::Result state;
    assert(exotica_state::setup(a,setup) && zeus_state::transition(seed,{},setup.packet,0x100,state));
    auto current=state.context;
    const std::vector<uint32_t> model={0x229d0000,1,0x36200000,0x05000100,0x38000000,0,0x0001ffff,0xffffffff,0,0,0,0,0xffff0001,0x00010001};
    exotica_endpoint::Result result;
    assert(exotica_endpoint::prepare(current,5000,0x100,6,0,model,a,result));
    assert(result.original.size()==1 && result.changed==1);
    assert(result.original[0].state[9]==30 && result.replacement[0].state[9]==28);
    assert(result.original[0].state[10]==2047 && result.replacement[0].state[10]==0);
    assert(result.original[0].vertices==result.replacement[0].vertices);
    const auto saved=result;
    auto reject=[&](const zeus_state::Context &c,const exotica_state::Operands &input,
        uint32_t frame,uint32_t base,uint32_t count,uint32_t policy,const std::vector<uint32_t> &words) {
        assert(!exotica_endpoint::prepare(c,frame,base,count,policy,words,input,result));
        assert(exotica_endpoint::same_quads(result.original,saved.original));
        assert(exotica_endpoint::same_quads(result.replacement,saved.replacement) && result.changed==saved.changed);
    };
    auto bad=a;bad.flags&=~uint32_t(0x04000000);reject(current,bad,5000,0x100,6,0,model);
    bad=a;bad.object[16]=0x04f81234;reject(current,bad,5000,0x100,6,0,model);
    bad=a;bad.object[16]=0x780c1234;reject(current,bad,5000,0x100,6,0,model); // original control differs
    bad=a;bad.object[18]++;reject(current,bad,5000,0x100,6,0,model); // different palette
    bad=a;bad.bodies[0][1]++;reject(current,bad,5000,0x100,6,0,model); // different program
    reject(current,a,0,0x100,6,0,model);reject(current,a,5000,0,6,0,model);
    reject(current,a,5000,0x100,7,0,model);reject(current,a,5000,0x100,6,1,model);
    auto invalid=current;invalid.matrix[0]=std::numeric_limits<float>::quiet_NaN();reject(invalid,a,5000,0x100,6,0,model);
    auto broken=model;broken[0]=0xff000000;reject(current,a,5000,0x100,6,0,broken);
    assert(a.flags==0x04000130 && a.object[16]==0x78081234 && current.matrix==seed.matrix);
    // Known static-light fade changes program, not packed model layout.
    a.flags=0x04008530;a.object[15]=a.flags;
    a.bodies[2][1]=0x22b;a.bodies[3][1]=0x29b;
    w(0xb4a1,0x40020202);a.constants[3]=0x40000000;
    assert(exotica_state::setup(a,setup) && setup.program==3 &&
        zeus_state::transition(seed,{},setup.packet,0x100,state));
    current=state.context;
    auto lit_model=model;lit_model.push_back(0);lit_model.push_back(0);
    assert(exotica_endpoint::prepare(current,5000,0x100,7,0,lit_model,a,result));
    assert(result.original.size()==1 && result.changed==1 && current.ucode==0x29b);
    assert(result.original[0].vertices==result.replacement[0].vertices);
    const auto lit_saved=result;
    auto last_program=current;last_program.regs[0x40]=0x38550075;
    assert(exotica_endpoint::prepare(last_program,5000,0x100,7,0,lit_model,a,result));
    assert(exotica_endpoint::same_quads(result.original,lit_saved.original) &&
        exotica_endpoint::same_quads(result.replacement,lit_saved.replacement));
    auto wrong_palette=last_program;++wrong_palette.palette;
    assert(!exotica_endpoint::prepare(wrong_palette,5000,0x100,7,0,lit_model,a,result));
    assert(exotica_endpoint::same_quads(result.replacement,lit_saved.replacement));
    for(unsigned mutation=0;mutation<5;++mutation) {
        bad=a;
        if(mutation==0)bad.bodies[2][1]=0xc0; // different layout
        if(mutation==1)bad.bodies[2][1]=0x324; // unqualified program
        if(mutation==2)bad.object[18]++; // changed palette
        if(mutation==3)bad.commands[0xb498-0xb479]^=0x20; // changed depth test
        if(mutation==4)bad.constants[3]=0x05000123; // changed texture binding
        assert(!exotica_endpoint::prepare(current,5000,0x100,7,0,lit_model,bad,result));
        assert(exotica_endpoint::same_quads(result.original,lit_saved.original) &&
            exotica_endpoint::same_quads(result.replacement,lit_saved.replacement));
    }
    std::cout<<"PASS private original-model endpoint, exact control and transactional rejections\n";
}
