// SPDX-License-Identifier: BSD-3-Clause
#include "exotica_scene.h"
#include "exotica_scene_capture.h"
#include <cassert>
#include <limits>
using namespace cruisn;
uint32_t bits(float v){uint32_t w;std::memcpy(&w,&v,4);return w;}
int main()
{
    auto f=[](int n){return scenery::Float::integer(n).store();};
    exotica_scene::Parameters p;p.frame=1;p.margin=88;p.scale=0xfa000000; // Synthetic 1/64.
    p.camera.fill(f(0));for(unsigned i=0;i<9;++i)p.view[i]=p.alternate[i]=f(i%4==0);
    auto &a=p.setup;
    auto w=[&](unsigned address,uint32_t value){a.commands[address-0xb479]=value;};
    w(0xb47b,0x32000000);w(0xb47c,0x1c000000);w(0xb481,0x05410000);w(0xb482,0x05400000);
    w(0xb493,0x05200000);w(0xb49d,0x15000000);
    a.constants[2]=0xc700;a.constants[6]=0x8100;
    for(unsigned i=0;i<4;++i){a.programs[i]=i+10;a.bodies[i]={{0x05410000,0xc0,0x05400000,0x50000}};}
    a.defaults={0x0c000100,0x14000000};a.palette_setup=0x0084003f;
    auto &c=p.context;c.regs[0x66]=0x8e;c.regs[0x68]=0x9d;c.regs[0x6c]=9;
    c.regs[0x6a]=bits(256);c.regs[0x6b]=bits(200);c.render[1]=511;c.render[2]=399;
    exotica_future::Source source;source.entry=0xa00000;source.source=0xc01000;
    source.supported=source.future=true;
    source.words[1]=source.words[2]=f(0);source.words[3]=f(100);
    std::copy(p.view.begin(),p.view.end(),source.words.begin()+5);
    source.words[17]=0xa10000;source.words[18]=0x10001;
    std::vector<uint32_t> model={0x229d0000,1,0x36200000,0x05000100,0x38000000,0,0x0001ffff,0xffffffff,0,0,0,0,0xffff0001,0x00010001};
    const auto original_model=model;
    std::map<uint32_t,uint32_t> memory={{0x67da,204800},{0x67db,p.scale},{0xa10000,0},{0xa10003,0x100},{0xa10004,6}};
    auto read=[&](uint32_t address){return memory.at(address);};
    unsigned reads=0;
    auto models=[&](uint32_t base,uint32_t count,std::vector<uint32_t> &output){
        ++reads;assert(base==0x100 && count==6);output=model;return true;};
    auto selected=[](const exotica_future::Source &s){return s.future;};
    exotica_scene::Result result;
    assert(exotica_scene::build({source},p,read,models,selected,result));
    assert(result.instances.size()==1 && result.quads.size()==1 && result.viewport_polygons==1);
    assert(result.instances[0].band==1 && result.instances[0].depth==100 && reads==1);
    assert(result.quads[0].state[0]==1 && result.quads[0].state[9]==28);
    const auto serialized=exotica_scene::parameter_words(p,2,true);
    assert(serialized[0]==0x31534358 && serialized[1]==1 && serialized[3]==bits(88));
    assert(serialized[5]==2 && serialized[6]==1 && serialized[7]==p.scale);
    const auto headers=exotica_scene::instance_words(result);
    assert(headers.size()==1 && headers[0][0]==source.entry && headers[0][9]==0 && headers[0][10]==1);
    assert(exotica_scene::byte_hash("hello",5)==UINT64_C(0xa430d84680aabd0b));
    assert((model==original_model && p.context.translation==std::array<float,4>{}));
    auto second=source;second.source+=6;second.words[1]=f(10);reads=0;
    assert(exotica_scene::build({source,second},p,read,models,selected,result));
    assert(result.instances.size()==2 && result.quads.size()==2 && reads==1 && result.model_words_read==14);
    assert(result.quads[0].vertices[0][0]!=result.quads[1].vertices[0][0]);
    assert(!exotica_scene::build({source,source},p,read,models,selected,result) && result.quads.empty());
    p.multiplier=3;
    for(auto item:{std::pair<int,uint32_t>{204800,1},{204801,2},{409600,2},{409601,3},{614400,3}})
    {
        auto s=source;s.words[3]=f(item.first);
        assert(exotica_scene::build({s},p,read,models,selected,result));
        assert(result.instances.size()==1 && result.instances[0].band==item.second);
    }
    auto outside=source;outside.words[3]=f(614401);
    assert(exotica_scene::build({outside},p,read,models,selected,result) && result.instances.empty() && result.culled_distance==1);
    auto invalid=source;invalid.source+=6;invalid.words[21]=UINT32_MAX;
    assert(!exotica_scene::build({source,invalid},p,read,models,selected,result) && result.quads.empty());
    invalid=source;invalid.words[15]=0x80;
    assert(exotica_scene::build({invalid},p,read,models,selected,result) && result.unsupported_transform==1);
    invalid=source;invalid.future=false;
    assert(exotica_scene::build({invalid},p,read,models,selected,result) && !result.selected);
    model.pop_back();assert(!exotica_scene::build({source},p,read,models,selected,result) && result.quads.empty());model=original_model;
    memory[0xa10004]=0xffffffff;
    assert(!exotica_scene::build({source},p,read,models,selected,result));memory[0xa10004]=6;
    model[3]=0x15000000;
    assert(!exotica_scene::build({source},p,read,models,selected,result));model=original_model;
    a.palette_setup=0x0084001f;
    assert(!exotica_scene::build({source},p,read,models,selected,result));a.palette_setup=0x0084003f;
    p.context.texture=0xabcdef;
    assert(exotica_scene::build({source},p,read,models,selected,result));
    assert(result.quads[0].state[3]==0x100);
    memory[0x67db]=0;
    assert(!exotica_scene::build({source},p,read,models,selected,result));memory[0x67db]=p.scale;
    p.render_policy=1;assert(!exotica_scene::build({source},p,read,models,selected,result));p.render_policy=0;
    p.margin=std::numeric_limits<float>::quiet_NaN();assert(!exotica_scene::build({source},p,read,models,selected,result));p.margin=88;
    std::vector<exotica_future::Source> too_many(exotica_scene::max_sources+1);
    assert(!exotica_scene::build(too_many,p,read,models,selected,result));
}
