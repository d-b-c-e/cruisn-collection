#include "world_active_roads.h"
#include <cassert>
#include <map>
int main()
{
    using cruisn::world_host::Descriptor;
    for(uint32_t revision:{24U,25U})
    {
        std::map<uint32_t,uint32_t> ram;
        const uint32_t heads24[]={0x61ee,0x61eb,0x61ed,0x61ef};
        const uint32_t heads25[]={0x658f,0x658c,0x658e,0x6590};
        const auto heads=revision==24?heads24:heads25;
        for(unsigned i=0;i<4;++i)
        {
            ram[0x69+3*i]=0x08280000|heads[i];ram[0x6a+3*i]=0x6200034c;
            ram[heads[i]]=0x1000+i;ram[0x1000+i]=0;
        }
        ram[0x1000]=0x1100;ram[0x1100]=0x1200;ram[0x110e]=0x10001001;
        ram[0x120e]=0x1000; // an ordinary active object is excluded
        auto read=[&](uint32_t p){assert(p<0x20000);return ram[p];};
        std::vector<Descriptor> out;
        assert(cruisn::world_active_roads::code_matches(read,revision));
        assert(!cruisn::world_active_roads::code_matches(read,23));
        assert(cruisn::world_active_roads::collect(read,out,revision) && out.size()==1);
        assert(out[0].id==0xc0001100 && out[0].active_margin && out[0].words[14]==0x10001001);
        const auto saved=out;
        // Changing allocation/list membership is observed on every collection.
        ram[0x1100]=0;out.clear();assert(cruisn::world_active_roads::collect(read,out,revision) && out.size()==1);
        ram[0x1000]=0;out.clear();assert(cruisn::world_active_roads::collect(read,out,revision) && out.empty());
        // Invalid topology cannot append a partially collected prefix.
        ram[0x1000]=0x1100;ram[0x1100]=0x1100;out=saved;
        assert(cruisn::world_active_roads::code_matches(read,revision));
        assert(!cruisn::world_active_roads::collect(read,out,revision) && out.size()==1);
        ram[0x1100]=0;ram[0x1001]=0x1100;
        assert(!cruisn::world_active_roads::collect(read,out,revision) && out.size()==1);
        ram[0x1001]=0;ram[0x110e]=0x2001;
        assert(cruisn::world_active_roads::collect(read,out,revision) && out.size()==1);
        ram[0x110e]=0x3020; // actual pre-race effect: valid list, no road admission
        assert(cruisn::world_active_roads::collect(read,out,revision) && out.size()==1);
        ram[0x110e]=0x1001;ram[0x1100]=0x900000;
        assert(!cruisn::world_active_roads::collect(read,out,revision) && out.size()==1);
        ram[0x1100]=0;ram[0x6a]^=1;
        assert(!cruisn::world_active_roads::code_matches(read,revision));
        assert(!cruisn::world_active_roads::collect(read,out,revision) && out.size()==1);
    }
}
