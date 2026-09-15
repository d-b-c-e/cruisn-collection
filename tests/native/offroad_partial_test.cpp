#include "offroad_partial_sections.h"
#include <cassert>
#include <map>
int main()
{
    using namespace cruisn::offroad_future;
    std::vector<uint32_t> ram(0x20000);std::map<uint32_t,uint32_t> rom;
    const uint32_t track=0xc10000,data=0xc11000,pool=0x1000;
    for(unsigned i=0;i<3;++i){rom[track+4*i]=(i==0?1:0)|(i==2?0x80000000U:0);rom[track+4*i+1]=i;}
    rom[track+7]=data;rom[data+16]=2;
    for(unsigned i=0;i<22;++i)rom[data+17+i]=0;
    rom[data+18]=rom[data+29]=0xc80000;
    ram[0x1b4b4]=ram[0x1b4b5]=ram[0x1b4b7]=ram[0x1b4ba]=track;
    ram[0x1b4cc]=3;ram[0x1b4bd]=1;ram[0x1b4b9]=1;ram[0x1b4cd]=0xc90000;
    ram[0x111ee]=pool;ram[0x111f6]=0x1b754;ram[0x1b754]=pool;
    for(unsigned i=0;i<1200;++i)ram[pool+22*i]=i+1<1200?pool+22*(i+1):0;
    auto read=[&](uint32_t p){return p<ram.size()?ram[p]:rom.at(p);};
    Result base;assert(frontier(read,base.frontier));assert(base.frontier.partial);
    auto out=base;assert(recover_partial(read,out) && out.sources.size()==2);
    const auto first=out.sources[0];assert(first.number==1 && first.ordinal==0);
    // An allocated identity is excluded regardless of different mutable fields.
    ram[0x1b754]=pool+22;ram[pool+6]=first.words[6];
    out=base;assert(recover_partial(read,out) && out.sources.size()==1 && out.sources[0].ordinal==1);
    // Reusing the same frontier must inspect fresh allocation membership.
    ram[pool+6]=out.sources[0].words[6];
    out=base;assert(recover_partial(read,out) && out.sources.size()==1 && out.sources[0].ordinal==0);
    auto snapshot=out;assert(!recover_partial(read,out) && out.sources.size()==snapshot.sources.size());
    assert(out.sources[0].source==snapshot.sources[0].source);
    // A broken free list or boundary fails before adding anything.
    ram[pool+22]=pool+22;out=base;assert(!recover_partial(read,out) && out.sources.empty());
    ram[pool+22]=pool+44;ram[0x1b754]=pool+1;assert(!recover_partial(read,out) && out.sources.empty());
    ram[0x1b754]=pool+22;ram[0x111f6]=0;assert(!recover_partial(read,out) && out.sources.empty());
    ram[0x111f6]=0x1b754;out=base;++out.frontier.current;assert(!recover_partial(read,out));
    // Unsupported source classes stay excluded. No ordinary relabeling.
    rom[data+17]=0x04000000;ram[pool+6]=0;
    out=base;assert(recover_partial(read,out) && out.sources.size()==1 && out.sources[0].ordinal==1);
    rom[data+28]=2;out=base;assert(recover_partial(read,out) && out.sources.empty());
    // Settled and end-of-track paths need no pool observation.
    out=base;out.frontier.partial=false;ram[0x111f6]=0;assert(recover_partial(read,out));
    out=base;out.frontier.front=2;assert(recover_partial(read,out) && out.sources.empty());
}
