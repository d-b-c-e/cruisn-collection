#include "world_road_scenery.h"
#include <cassert>
#include <map>
#include <stdexcept>
int main()
{
    using namespace cruisn::world_road;
    // Different polygon counts/UV addresses in the two codecs; shared vertices.
    std::map<uint32_t,uint32_t> m={{0xc10000,2500},{0xc10001,0xc20000},
        {0xc10002,(1U<<18)|8},{0xd4c0,15000},{0x624,0x600},
        {0x601,0x700},{0x700,4},{0x701,0x800}};
    auto read=[&](uint32_t p){auto i=m.find(p);if(i==m.end())throw std::runtime_error("unexpected read");return i->second;};
    const auto original=m;
    std::array<uint32_t,32> obj{};obj[13]=0xc10000;obj[14]=0x2001;obj[15]=0x2300;
    Model out;
    assert(select(read,obj,14999,out) && !out.far_template && out.selected==0xc10000);
    assert(out.vertices==8 && out.polygons==2 && out.vertex_data==0xc10003 && out.polygon_data==0xc10013);
    assert(select(read,obj,15000,out) && out.far_template && out.selected==0x700);
    assert(out.vertices==4 && out.polygons==1 && out.vertex_data==0xc10003 && out.polygon_data==0x702 && out.materials==0x800);
    assert(m==original);
    obj[15]=0x300;assert(!select(read,obj,24000,out));obj[15]=0x2300;
    m[0x624]=0x993000;assert(!select(read,obj,24000,out));m[0x624]=0x600;
    m[0x601]=0x1ffff;assert(!select(read,obj,24000,out));m[0x601]=0x700;
    m[0x700]=0x104;assert(!select(read,obj,24000,out));m[0x700]=4;
    m[0x701]=0x1ffff;assert(!select(read,obj,24000,out));m[0x701]=0x800;
    obj[13]=0xfffffe;assert(!select(read,obj,24000,out));obj[13]=0xc10000;
    obj[14]|=0x800;assert(!select(read,obj,24000,out));
}
