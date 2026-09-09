// license:BSD-3-Clause
// Read-only World road model selection. No road-chain/physics initialization.
#pragma once
#include <array>
#include <cstdint>

namespace cruisn { namespace world_road {
struct Model
{
    uint32_t selected=0,radius=0,header=0,vertices=0,polygons=0;
    uint32_t vertex_data=0,polygon_data=0,materials=0;
    bool far_template=false;
};
inline bool rom(uint32_t p,uint32_t n)
{return p>=0xc00000 && n<=4096 && uint64_t(p)+n<=0x1000000;}
inline bool ram(uint32_t p,uint32_t n)
{return n<=4096 && uint64_t(p)+n<=0x20000;}
template<class Read> bool code_matches(Read read)
{
    static const uint32_t code[][2]={{0x62c,0x04a1d4c0},{0x635,0x152fd4bf},
        {0x638,0x08412101},{0x641,0x082b0049},{0x677,0x04f21387},
        {0x67d,0x24c00182},{0x683,0x6a20fb9d},{0x241,0x082ed4bf},{0x2e0,0x082ed4bf},
        {0x7c1b,0x0821d58d},{0x7c1d,0x04e00b00},{0x7c21,0x02e1f000},
        {0x7c22,0x10610300},{0x7c23,0x1541040f},{0x7c27,0x0822d57d},
        {0x7c28,0x1a620008},{0x7c30,0x08600001},{0x7c39,0x08610001}};
    for(auto const &v:code)if(read(v[0])!=v[1])return false;
    return true;
}
template<class Read> bool select(Read read,const std::array<uint32_t,32> &obj,int32_t depth,Model &out)
{
    if((obj[14]&0x801)!=1 || !rom(obj[13],3))return false;
    out=Model{};
    out.radius=read(obj[13]);out.vertex_data=obj[13]+3;
    out.far_template=depth>=int32_t(read(0xd4c0));
    if(out.far_template)
    {
        const uint32_t ordinal=(obj[15]>>12)&15;
        if(!ordinal)return false;
        uint32_t table=read(0x624);
        if(!ram(table,15))return false;
        out.selected=read(table+ordinal-1);
        if(!ram(out.selected,2))return false;
        out.header=read(out.selected);out.materials=read(out.selected+1);
        out.polygon_data=out.selected+2;
    }
    else
    {
        out.selected=obj[13];out.header=read(obj[13]+2);out.materials=read(obj[13]+1);
        out.polygon_data=obj[13]+3+2*(out.header&255);
    }
    // Road vertices come from the original ROM model even when the polygon
    // and UV list switches to a small RAM template. Paired packing is a
    // different codec and is never inferred from a template's vertex count.
    if(out.header&0x300)return false;
    out.vertices=out.header&255;out.polygons=(out.header>>18)+1;
    if(!out.vertices || out.vertices>256 || out.polygons>1024 ||
        !rom(out.vertex_data,2*out.vertices))return false;
    if(out.far_template)
        return ram(out.polygon_data,2*out.polygons) && ram(out.materials,3*out.polygons);
    return rom(out.polygon_data,2*out.polygons) && rom(out.materials,3*out.polygons);
}
} }
